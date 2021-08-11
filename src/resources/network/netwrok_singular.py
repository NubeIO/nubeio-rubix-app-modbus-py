from flask_restful import reqparse
from flask_restful.reqparse import request
from rubix_http.exceptions.exception import NotFoundException

from src.models.model_network import NetworkModel
from src.resources.network.network_base import NetworkBaseResource, modbus_network_marshaller
from src.resources.rest_schema.schema_network import network_all_attributes


class NetworkSingularResource(NetworkBaseResource):
    patch_parser = reqparse.RequestParser()
    for attr in network_all_attributes:
        patch_parser.add_argument(attr,
                                  type=network_all_attributes[attr].get('type'),
                                  required=False,
                                  store_missing=False)

    @classmethod
    def get(cls, **kwargs):
        network: NetworkModel = cls.find_network(**kwargs)
        if not network:
            raise NotFoundException('Modbus Network not found')
        return modbus_network_marshaller(network, request.args)

    # TODO: don't allow type in patch
    @classmethod
    def put(cls, **kwargs):
        data = cls.parser.parse_args()
        network: NetworkModel = cls.find_network(**kwargs)
        if network is None:
            return modbus_network_marshaller(cls.add_network(data), request.args)
        network.update(**data)
        return modbus_network_marshaller(cls.find_network(**kwargs), request.args)

    @classmethod
    def patch(cls, **kwargs):
        data = cls.patch_parser.parse_args()
        network: NetworkModel = cls.find_network(**kwargs)
        if network is None:
            raise NotFoundException(f"Does not exist {kwargs}")
        network.update(**data)
        return modbus_network_marshaller(cls.find_network(**kwargs), request.args)

    @classmethod
    def delete(cls, **kwargs):
        network: NetworkModel = cls.find_network(**kwargs)
        if not network:
            raise NotFoundException(f"Not found {kwargs}")
        network.delete_from_db()
        return '', 204

    @classmethod
    def find_network(cls, **kwargs) -> NetworkModel:
        raise NotImplementedError


class NetworkSingularResourceByUUID(NetworkSingularResource):
    @classmethod
    def find_network(cls, **kwargs) -> NetworkModel:
        return NetworkModel.find_by_uuid(kwargs.get('uuid'))


class NetworkSingularResourceByName(NetworkSingularResource):
    @classmethod
    def find_network(cls, **kwargs) -> NetworkModel:
        return NetworkModel.find_by_name(kwargs.get('name'))
