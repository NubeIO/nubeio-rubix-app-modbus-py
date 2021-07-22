from flask_restful import reqparse
from flask_restful.reqparse import request
from rubix_http.exceptions.exception import NotFoundException

from src.models.device.device import DeviceModel
from src.resources.device.device_base import DeviceBaseResource, device_marshaller
from src.resources.rest_schema.schema_device import device_all_attributes


class DeviceSingularResource(DeviceBaseResource):
    patch_parser = reqparse.RequestParser()
    for attr in device_all_attributes:
        patch_parser.add_argument(attr,
                                  type=device_all_attributes[attr]['type'],
                                  required=False,
                                  store_missing=False)

    @classmethod
    def get(cls, **kwargs):
        device: DeviceModel = cls.get_device(**kwargs)
        if not device:
            raise NotFoundException('Device not found')
        return device_marshaller(device, request.args)

    @classmethod
    def put(cls, **kwargs):
        data = cls.parser.parse_args()
        device: DeviceModel = cls.get_device(**kwargs)
        if device is None:
            return device_marshaller(cls.add_device(data), request.args)

        device.update(**data)
        return device_marshaller(cls.get_device(**kwargs), request.args)

    @classmethod
    def patch(cls, **kwargs):
        data = cls.patch_parser.parse_args()
        device: DeviceModel = cls.get_device(**kwargs)
        if device is None:
            raise NotFoundException(f"Does not exist {kwargs}")
        device.update(**data)
        return device_marshaller(cls.get_device(**kwargs), request.args)

    @classmethod
    def delete(cls, **kwargs):
        device: DeviceModel = cls.get_device(**kwargs)
        if not device:
            raise NotFoundException(f'Not found {kwargs}')
        device.delete_from_db()
        return '', 204

    @classmethod
    def get_device(cls, **kwargs) -> DeviceModel:
        raise NotImplementedError


class DeviceSingularResourceByUUID(DeviceSingularResource):
    @classmethod
    def get_device(cls, **kwargs) -> DeviceModel:
        return DeviceModel.find_by_uuid(kwargs.get('uuid'))


class DeviceSingularResourceByName(DeviceSingularResource):
    @classmethod
    def get_device(cls, **kwargs) -> DeviceModel:
        return DeviceModel.find_by_name(kwargs.get('network_name'), kwargs.get('device_name'))
