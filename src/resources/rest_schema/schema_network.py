from copy import deepcopy

from flask_restful import fields

from src.resources.rest_schema.schema_device import device_all_fields_with_children, device_all_fields
from src.resources.utils import map_rest_schema

network_all_attributes = {
    'name': {
        'type': str,
        'required': True,
    },
    'enable': {
        'type': bool,
        'required': True,
    },
    'fault': {
        'type': bool,
    },
    'tags': {
        'type': str
    },
    'rtu_port': {
        'type': str,
    },
    'rtu_speed': {
        'type': int,
    },
    'rtu_stop_bits': {
        'type': int,
    },
    'rtu_parity': {
        'type': str,
        'nested': True,
        'dict': 'rtu_parity.name'
    },
    'rtu_byte_size': {
        'type': int,
    },
    'tcp_ip': {
        'type': str,
    },
    'tcp_port': {
        'type': int,
    },
    'type': {
        'type': str,
        'required': True,
        'nested': True,
        'dict': 'type.name'
    },
    'timeout': {
        'type': int,
    },
    'polling_interval_runtime': {
        'type': int,
    },
    'point_interval_ms_between_points': {
        'type': int,
    }
}

network_return_attributes = {
    'uuid': {
        'type': str,
    },
    'created_on': {
        'type': str,
    },
    'updated_on': {
        'type': str,
    }
}


network_all_fields = {}
map_rest_schema(network_return_attributes, network_all_fields)
map_rest_schema(network_all_attributes, network_all_fields)

network_all_fields_with_children = deepcopy(network_all_fields)
network_all_fields_with_children['devices'] = fields.List(fields.Nested(device_all_fields_with_children))

network_all_fields_without_point_children = deepcopy(network_all_fields)
network_all_fields_without_point_children['devices'] = fields.List(fields.Nested(device_all_fields))
