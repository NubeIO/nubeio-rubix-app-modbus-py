from collections import OrderedDict

from flask_restful import fields, reqparse

from src.resources.utils import map_rest_schema

priority_array_write_fields = OrderedDict({
    '_1': fields.Float,
    '_2': fields.Float,
    '_3': fields.Float,
    '_4': fields.Float,
    '_5': fields.Float,
    '_6': fields.Float,
    '_7': fields.Float,
    '_8': fields.Float,
    '_9': fields.Float,
    '_10': fields.Float,
    '_11': fields.Float,
    '_12': fields.Float,
    '_13': fields.Float,
    '_14': fields.Float,
    '_15': fields.Float,
    '_16': fields.Float,
})

point_store_fields = {
    'point_uuid': fields.String,
    'value': fields.Float,
    'value_original': fields.Float,
    'value_raw': fields.String,
    'fault': fields.Boolean,
    'fault_message': fields.String,
    'ts_value': fields.String,
    'ts_fault': fields.String
}

point_all_attributes = {
    'device_uuid': {
        'type': str,
        'required': True,
    },
    'name': {
        'type': str,
        'required': True,
    },
    'enable': {
        'type': bool,
        'required': True,
    },
    'writable': {
        'type': bool,
    },
    'priority_array_write': {
        'type': dict,
    },
    'cov_threshold': {
        'type': float,
    },
    'value_round': {
        'type': int,
    },
    'value_operation': {
        'type': str
    },
    'input_min': {
        'type': float,
    },
    'input_max': {
        'type': float,
    },
    'scale_min': {
        'type': float,
    },
    'scale_max': {
        'type': float,
    },
    'tags': {
        'type': str
    },
    'fallback_value': {
        'type': float,
    },
    'register': {
        'type': int,
        'required': True,
    },
    'register_length': {
        'type': int,
        'required': True,
    },
    'function_code': {
        'type': str,
        'required': True,
        'nested': True,
        'dict': 'function_code.name'
    },
    'data_type': {
        'type': str,
        'nested': True,
        'dict': 'data_type.name'
    },
    'data_endian': {
        'type': str,
        'nested': True,
        'dict': 'data_endian.name'
    },
    'write_value_once': {
        'type': bool,
    }
}

point_return_attributes = {
    'uuid': {
        'type': str,
    },
    'created_on': {
        'type': str,
    },
    'updated_on': {
        'type': str,
    },
    'priority_array_write': {
        'type': fields.Nested(priority_array_write_fields),
    },
    'point_store': {
        'type': fields.Nested(point_store_fields),
    }
}

point_all_fields = {}
map_rest_schema(point_all_attributes, point_all_fields)
map_rest_schema(point_return_attributes, point_all_fields)

poll_non_existing_attributes = {
    'network_rtu_port': {
        'type': str,
    },
    'network_rtu_speed': {
        'type': int,
    },
    'network_rtu_stop_bits': {
        'type': int,
    },
    'network_rtu_parity': {
        'type': str,
    },
    'network_rtu_byte_size': {
        'type': int,
    },
    'network_tcp_ip': {
        'type': str,
    },
    'network_tcp_port': {
        'type': int,
    },
    'network_type': {
        'type': str,
        'required': True
    },
    'network_timeout': {
        'type': int,
    },
    'device_address': {
        'type': int,
        'required': True
    },
    'device_zero_based': {
        'type': bool,
    },
    'point_register': {
        'type': int,
        'required': True
    },
    'point_register_length': {
        'type': int,
        'required': True
    },
    'point_function_code': {
        'type': str,
        'required': True
    },
    'point_priority_array_write': {
        'type': dict,
    },
    'point_data_type': {
        'type': str,
    },
    'point_data_endian': {
        'type': str,
    },
}


def add_nested_priority_array_write():
    nested_priority_array_write_parser = reqparse.RequestParser()
    nested_priority_array_write_parser.add_argument('_1', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_2', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_3', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_4', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_5', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_6', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_7', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_8', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_9', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_10', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_11', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_12', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_13', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_14', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_15', type=float, location=('priority_array_write',))
    nested_priority_array_write_parser.add_argument('_16', type=float, location=('priority_array_write',))
