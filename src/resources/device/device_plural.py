from flask_restful.reqparse import request

from src.models.model_device import DeviceModel
from src.resources.device.device_base import DeviceBaseResource, device_marshaller


class DevicePluralResource(DeviceBaseResource):
    @classmethod
    def get(cls):
        return device_marshaller(DeviceModel.find_all(), request.args)

    @classmethod
    def post(cls):
        data = DevicePluralResource.parser.parse_args()
        return device_marshaller(cls.add_device(data), request.args)
