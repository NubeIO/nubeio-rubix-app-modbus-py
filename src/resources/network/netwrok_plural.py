from flask_restful.reqparse import request

from src.models.model_network import NetworkModel
from src.resources.network.network_base import NetworkBaseResource, modbus_network_marshaller


class NetworkPluralResource(NetworkBaseResource):
    @classmethod
    def get(cls):
        return modbus_network_marshaller(NetworkModel.find_all(), request.args)

    @classmethod
    def post(cls):
        data = NetworkPluralResource.parser.parse_args()
        return modbus_network_marshaller(cls.add_network(data), request.args)
