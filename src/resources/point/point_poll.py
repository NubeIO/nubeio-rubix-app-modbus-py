from flask_restful import reqparse, marshal_with
from rubix_http.exceptions.exception import NotFoundException
from rubix_http.resource import RubixResource

from src.enums.network import ModbusType
from src.models.model_device import DeviceModel
from src.models.model_network import NetworkModel
from src.models.model_point import PointModel
from src.resources.rest_schema.schema_point import poll_non_existing_attributes, \
    point_store_fields, point_all_fields
from src.services.polling.modbus_polling import RtuPolling, TcpPolling
from src.models.model_priority_array import PriorityArrayModel


class PointPollResource(RubixResource):
    @classmethod
    @marshal_with(point_all_fields)
    def get(cls, uuid: str):
        point: PointModel = PointModel.find_by_uuid(uuid)
        if not point:
            raise NotFoundException('Modbus Point not found')
        else:
            if point.device.type == ModbusType.RTU:
                return RtuPolling().poll_point(point)
            else:
                return TcpPolling().poll_point(point)


class PointPollNonExistingResource(RubixResource):
    parser = reqparse.RequestParser()
    for attr in poll_non_existing_attributes:
        parser.add_argument(attr,
                            type=poll_non_existing_attributes[attr]['type'],
                            required=poll_non_existing_attributes[attr].get('required', False),
                            store_missing=False)

    @classmethod
    @marshal_with(point_store_fields)
    def post(cls):
        data = cls.parser.parse_args()
        network_data = {k.replace('network_', ''): v for k, v in data.items() if 'network_' in k}
        device_data = {k.replace('device_', ''): v for k, v in data.items() if 'device_' in k}
        point_data = {k.replace('point_', ''): v for k, v in data.items() if 'point_' in k}

        network = NetworkModel.create_temporary(**network_data)
        device = DeviceModel.create_temporary(**device_data)
        priority_array_write: dict = point_data.pop('priority_array_write', {})
        point = PointModel.create_temporary(
            priority_array_write=PriorityArrayModel.create_priority_array_model(None, priority_array_write,
                                                                                point_data.get('fallback_value')),
            **point_data)
        network.check_self()
        device.check_self()
        point.check_self()

        if device.type == ModbusType.RTU:
            return RtuPolling().poll_point_not_existing(point, device, network)
        else:
            return TcpPolling().poll_point_not_existing(point, device, network)
