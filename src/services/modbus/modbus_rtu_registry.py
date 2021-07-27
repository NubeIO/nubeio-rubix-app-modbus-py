import logging

from pymodbus.client.sync import ModbusSerialClient as SerialClient

from src.models.network.network import NetworkModel, ModbusType
from src.services.modbus.modbus_registry import ModbusRegistry, ModbusRegistryConnection, \
    ModbusRegistryKey

logger = logging.getLogger(__name__)


class ModbusRtuRegistryKey(ModbusRegistryKey):
    def __init__(self, network: NetworkModel):
        self.__port: str = network.rtu_port
        self.__rtu_speed: int = network.rtu_speed
        self.__rtu_stop_bits: int = network.rtu_stop_bits
        self.__rtu_parity: str = network.rtu_parity.name
        self.__rtu_byte_size: int = network.rtu_byte_size
        self.__timeout: int = network.timeout
        super().__init__(network)

    def create_connection_key(self) -> str:
        return f'{self.__port}:{self.__rtu_speed}:{self.__rtu_stop_bits}:{self.__rtu_parity}:{self.__rtu_byte_size}:' \
               f'{self.__timeout}'


class ModbusRtuRegistry(ModbusRegistry):

    # TODO retries=0, retry_on_empty=False fix these up
    def add_connection(self, network: NetworkModel) -> ModbusRegistryConnection:
        port: str = network.rtu_port
        rtu_speed: int = network.rtu_speed
        rtu_stop_bits: int = network.rtu_stop_bits
        rtu_parity: str = network.rtu_parity.name
        rtu_byte_size: int = network.rtu_byte_size
        timeout: int = network.timeout

        registry_key: ModbusRtuRegistryKey = ModbusRtuRegistryKey(network)
        method = 'rtu'
        self.remove_connection_if_exist(registry_key.key)
        logger.debug(f'Adding rtu_connection {registry_key.key}')

        self.connections[registry_key.key] = ModbusRegistryConnection(
            registry_key.connection_key,
            SerialClient(method=method, port=port, baudrate=rtu_speed, stopbits=rtu_stop_bits,
                         parity=rtu_parity, bytesize=rtu_byte_size, timeout=timeout, retries=0, retry_on_empty=False)
        )
        self.connections[registry_key.key].client.connect()
        return self.connections[registry_key.key]

    def get_registry_key(self, network: NetworkModel) -> ModbusRegistryKey:
        return ModbusRtuRegistryKey(network)

    def get_type(self) -> ModbusType:
        return ModbusType.RTU
