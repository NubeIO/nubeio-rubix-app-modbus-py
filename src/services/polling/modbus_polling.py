import logging
import time
from abc import abstractmethod
from copy import deepcopy
from typing import Union, List

from gevent import sleep
from pymodbus.client.sync import BaseModbusClient
from pymodbus.exceptions import ConnectionException, ModbusIOException
from sqlalchemy.orm.exc import ObjectDeletedError

from src import db, FlaskThread
from src.enums.point import ModbusFunctionCode
from src.models.model_device import DeviceModel
from src.models.model_network import NetworkModel, ModbusType
from src.models.model_point import PointModel
from src.services.modbus_registry import ModbusRegistryConnection, ModbusRegistry
from src.services.modbus_rtu_registry import ModbusRtuRegistry
from src.services.modbus_tcp_registry import ModbusTcpRegistry, ModbusTcpRegistryKey
from src.services.polling.poll import poll_point, poll_point_aggregate
from src.models.model_point_store import PointStoreModel
from src.models.model_priority_array import PriorityArrayModel
from src.utils import Singleton

logger = logging.getLogger(__name__)


class ModbusPolling(metaclass=Singleton):
    __polling_interval: int = 2
    __count: int = 0

    def __init__(self, network_type: ModbusType):
        self.__network_type = network_type

    def polling(self):
        sleep(1)
        self.__log_info("Polling started")
        while True:
            self.__poll()
            sleep(ModbusPolling.__polling_interval)

    def __poll(self):
        self.__count += 1
        self.__log_debug(f'Poll loop {self.__count}...')
        networks: List[NetworkModel] = self.__get_all_networks()
        available_keys: List[str] = []
        for network in networks:
            registry_key = ModbusTcpRegistryKey(network)  # you can use TCP or RTU, choice is yours
            available_keys.append(registry_key.key)
            self.__poll_network(network)

        keys: List[str] = list(self.get_registry().get_connections().keys())
        for key in deepcopy(keys):
            if key not in available_keys:
                self.get_registry().remove_connection_if_exist(key)
        db.session.commit()

    def __poll_network(self, network: NetworkModel):
        current_connection: ModbusRegistryConnection = self.get_registry().add_edit_and_get_connection(network)
        if not current_connection.is_running:
            FlaskThread(target=self.__poll_network_thread, daemon=True,
                        kwargs={'network': network}).start()

    def __poll_network_thread(self, network: NetworkModel):
        """
        Poll connection points on a thread
        """
        self.__log_debug(f'Starting thread for {network}')
        while True:
            current_connection: Union[ModbusRegistryConnection, None] = \
                self.get_registry().get_connection(network)
            if not current_connection:
                self.__log_debug(f'Stopping thread for {network}, no connection')
                break
            network: Union[NetworkModel, None] = self.__get_network(network.uuid)
            if not network:
                self.__log_debug(f'Stopping thread for {network}, network not found')
                return
            try:
                self.__poll_network_devices(current_connection, network)
                db.session.commit()
            except Exception as e:
                self.__log_error(str(e))
            time.sleep(network.polling_interval_runtime)

    def __poll_network_devices(self, current_connection, network: NetworkModel):
        current_connection.is_running = True
        devices: List[DeviceModel] = self.__get_network_devices(network.uuid)
        for device in devices:
            if not self.__ping_point(current_connection, network, device):
                # we suppose that device is offline, so we are not wasting time for looping
                continue
            points: List[PointModel] = self.__get_all_device_points(device.uuid)

            if not device.supports_multiple_rw:
                self.__log_debug(f'Device {device.uuid} aggregate R/W UNSUPPORTED')
                for point in points:
                    try:
                        if not self.is_point_to_be_written(point):
                            continue
                        self.__poll_point(current_connection.client, network, device, [point])
                    except ConnectionException:
                        return
                    except ModbusIOException:
                        pass
            else:
                self.__log_debug(f'Device {device.uuid} aggregate R/W SUPPORTED')
                """
                group and sort points into corresponding FCs
                """
                fc_lists: List[List[PointModel]] = [[], [], [], [], [], []]

                for point in points:
                    if point.function_code is ModbusFunctionCode.READ_COILS:
                        fc_lists[0].append(point)
                    elif point.function_code is ModbusFunctionCode.READ_DISCRETE_INPUTS:
                        fc_lists[1].append(point)
                    elif point.function_code is ModbusFunctionCode.READ_HOLDING_REGISTERS:
                        fc_lists[2].append(point)
                    elif point.function_code is ModbusFunctionCode.READ_INPUT_REGISTERS:
                        fc_lists[3].append(point)
                    elif point.function_code is ModbusFunctionCode.WRITE_COIL or \
                            point.function_code is ModbusFunctionCode.WRITE_COILS:
                        fc_lists[4].append(point)
                    elif point.function_code is ModbusFunctionCode.WRITE_REGISTER or \
                            point.function_code is ModbusFunctionCode.WRITE_REGISTERS:
                        fc_lists[5].append(point)
                    else:
                        raise Exception(f'FC {point.function_code} unsupported for aggregate')

                # not the most efficient in respect to polling loop time (i.e. lora netowrks)
                #  but most efficient in respect to wear on end device individual register writes
                fc_lists[4][:] = [p for p in fc_lists[4] if self.is_point_to_be_written(p)]
                fc_lists[5][:] = [p for p in fc_lists[5] if self.is_point_to_be_written(p)]

                for fc_list in fc_lists:
                    fc_list.sort(key=lambda p: p.register)

                    last_point = 0
                    response_size = 0
                    for i in range(len(fc_list)):
                        response_size += fc_list[i].register_length
                        next_reg = 0
                        if i < len(fc_list) - 1:
                            next_reg: int = fc_list[i].register + fc_list[i].register_length

                        """
                        if - end of list
                           - response size limit reached
                           - next point is not continuous from current point
                        """
                        if i == len(fc_list) - 1 or response_size + fc_list[i + 1].register_length >= 253 or \
                                fc_list[i + 1].register != next_reg:
                            try:
                                if last_point == i:
                                    self.__log_debug(f'Polling SINGLE FC {fc_list[i].function_code}')
                                    self.__poll_point(current_connection.client, network, device, fc_list[i:i + 1])
                                    last_point += 1
                                else:
                                    self.__log_debug(f'Polling AGGREGATE FC {fc_list[i].function_code}')
                                    self.__poll_point(current_connection.client, network, device,
                                                      fc_list[last_point:i + 1])
                                    last_point = i + 1
                                response_size = 0
                            except ConnectionException:
                                return
                            except ModbusIOException:
                                pass
                        else:
                            continue

    def __ping_point(self, current_connection: ModbusRegistryConnection, network: NetworkModel,
                     device: DeviceModel) -> bool:
        """
        Poll connection points
        Checks whether the pinging point is fine or not?
        """
        if device.ping_point:
            try:
                ping_point = PointModel.create_temporary_from_string(device.ping_point)
                self.__poll_point(current_connection.client, network, device, [ping_point], True, False)
            except (ConnectionException, ModbusIOException):
                return False
            except ValueError as e:
                logger.error(f'Modbus device ping_point error: {e}')
                return False
        return True

    def __get_all_networks(self) -> List[NetworkModel]:
        return NetworkModel.query.filter_by(type=self.__network_type, enable=True).all()

    @staticmethod
    def __get_network(network_uuid: str) -> Union[NetworkModel, None]:
        return NetworkModel.query.filter_by(uuid=network_uuid, enable=True).first()

    @staticmethod
    def __get_network_devices(network_uuid: str) -> List[DeviceModel]:
        return DeviceModel.query.filter_by(network_uuid=network_uuid, enable=True).all()

    @staticmethod
    def __get_all_device_points(device_uuid: str) -> List[PointModel]:
        return PointModel.query.filter_by(device_uuid=device_uuid, enable=True).all()

    def poll_point_not_existing(self, point: PointModel, device: DeviceModel, network: NetworkModel):
        self.__log_debug(f'Manual poll request Non Existing Point {point}')
        connection: ModbusRegistryConnection = self.get_registry().add_edit_and_get_connection(network)
        point_store = self.__poll_point(connection.client, network, device, [point], False, False)
        return point_store

    def poll_point(self, point: PointModel) -> PointModel:
        self.__log_debug(f'Manual poll request {point}')
        device: DeviceModel = DeviceModel.find_by_uuid(point.device_uuid)
        network: NetworkModel = NetworkModel.find_by_uuid(device.network_uuid)
        self.__log_debug(f'Manual poll request: network: {network.uuid}, device: {device.uuid}, point: {point.uuid}')
        connection: ModbusRegistryConnection = self.get_registry().add_edit_and_get_connection(network)
        self.__poll_point(connection.client, network, device, [point])
        return point

    @staticmethod
    def __poll_point(client: BaseModbusClient, network: NetworkModel, device: DeviceModel,
                     point_list: List[PointModel], update_device_and_network: bool = True,
                     update_point_store: bool = True) -> Union[PointStoreModel, None]:
        point_store: Union[PointStoreModel, None] = None
        if update_device_and_network:
            if len(point_list) > 0:
                try:
                    error = None
                    try:
                        if len(point_list) == 1:
                            point_store = poll_point(client, network, device, point_list[0], update_point_store)
                        elif len(point_list) > 1:
                            poll_point_aggregate(client, network, device, point_list)
                        else:
                            raise Exception("Invalid __poll_point point_list length")
                    except ConnectionException as e:
                        if not network.fault:
                            network.set_fault(True)
                        error = e
                    except ModbusIOException as e:
                        if not device.fault:
                            device.set_fault(True)
                        error = e

                    if network.fault and not isinstance(error, ConnectionException):
                        network.set_fault(False)
                    elif device.fault and not isinstance(error, ModbusIOException) and \
                            not isinstance(error, ConnectionException):
                        device.set_fault(False)

                    if error is not None:
                        raise error
                except ObjectDeletedError:
                    return None
                time.sleep(float(network.point_interval_ms_between_points) / 1000)
        else:
            point_store = poll_point(client, network, device, point_list[0], update_point_store)
            time.sleep(float(network.point_interval_ms_between_points) / 1000)
        return point_store

    @staticmethod
    def is_point_to_be_written(point: PointModel) -> bool:
        write_value: float = PriorityArrayModel.get_highest_priority_value_from_priority_array(
            point.priority_array_write)
        return not((point.is_writable(point.function_code) and write_value is None) or (
            point.is_writable(point.function_code) and point.write_value_once and
            point.point_store is not None and not point.point_store.fault and
            point.point_store.value_original == write_value))

    @abstractmethod
    def get_registry(self) -> ModbusRegistry:
        raise NotImplementedError

    def __log_info(self, message: str):
        logger.info(f'{self.__network_type.name}: {message}')

    def __log_error(self, message: str):
        logger.error(f'{self.__network_type.name}: {message}')

    def __log_debug(self, message: str):
        logger.debug(f'{self.__network_type.name}: {message}')


class RtuPolling(ModbusPolling):

    def __init__(self):
        super().__init__(ModbusType.RTU)

    @abstractmethod
    def get_registry(self) -> ModbusRegistry:
        return ModbusRtuRegistry()


class TcpPolling(ModbusPolling):

    def __init__(self):
        super().__init__(ModbusType.TCP)

    @abstractmethod
    def get_registry(self) -> ModbusRegistry:
        return ModbusTcpRegistry()
