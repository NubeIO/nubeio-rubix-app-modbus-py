import random
import re

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import validates

from src import db
from src.enums.drivers import Drivers
from src.enums.point import ModbusFunctionCode, ModbusDataType, ModbusDataEndian
from src.models.model_network import NetworkModel
from src.models.model_point_store import PointStoreModel
from src.models.model_priority_array import PriorityArrayModel

from src.models.model_base import ModelBase
from src.utils.math_functions import eval_arithmetic_expression, eval_arithmetic_equation
from src.utils.model_utils import validate_json, get_highest_priority_value_from_priority_array


class PointModel(ModelBase):
    __tablename__ = 'points'
    uuid = db.Column(db.String(80), primary_key=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    device_uuid = db.Column(db.String, db.ForeignKey('devices.uuid'), nullable=False)
    enable = db.Column(db.Boolean(), nullable=False, default=True)
    writable = db.Column(db.Boolean, nullable=False, default=True)
    priority_array_write = db.relationship('PriorityArrayModel',
                                           backref='point',
                                           lazy=True,
                                           uselist=False,
                                           cascade="all,delete")
    cov_threshold = db.Column(db.Float, nullable=False, default=0)
    value_round = db.Column(db.Integer(), nullable=False, default=2)
    value_operation = db.Column(db.String, nullable=True, default="x + 0")
    input_min = db.Column(db.Float())
    input_max = db.Column(db.Float())
    scale_min = db.Column(db.Float())
    scale_max = db.Column(db.Float())
    tags = db.Column(db.String(320), nullable=True)
    point_store = db.relationship('PointStoreModel', backref='point', lazy=True, uselist=False, cascade="all,delete")
    fallback_value = db.Column(db.Float(), nullable=True)
    register = db.Column(db.Integer(), nullable=False)
    register_length = db.Column(db.Integer(), nullable=False)
    function_code = db.Column(db.Enum(ModbusFunctionCode), nullable=False)
    data_type = db.Column(db.Enum(ModbusDataType), nullable=False, default=ModbusDataType.RAW)
    data_endian = db.Column(db.Enum(ModbusDataEndian), nullable=False, default=ModbusDataEndian.BEB_LEW)
    write_value_once = db.Column(db.Boolean(), nullable=False, default=False)
    mp_gbp_mapping = db.relationship('MPGBPMapping', backref='point', lazy=True, uselist=False, cascade="all,delete")

    __table_args__ = (
        UniqueConstraint('name', 'device_uuid'),
        UniqueConstraint('register', 'function_code', 'device_uuid'),
    )

    def __repr__(self):
        return f"Point(uuid = {self.uuid})"

    @validates('name')
    def validate_name(self, _, value):
        if not re.match("^([A-Za-z0-9_-])+$", value):
            raise ValueError("name should be alphanumeric and can contain '_', '-'")
        return value

    @validates('value_operation')
    def validate_value_operation(self, _, value):
        try:
            if value and value.strip():
                eval_arithmetic_expression(value.lower().replace('x', str(random.randint(1, 9))))
        except Exception:
            raise ValueError("Invalid value_operation, must be a valid arithmetic expression")
        return value

    @validates('tags')
    def validate_tags(self, _, value):
        """
        Rules for tags:
        - force all tags to be lower case
        - if there is a gap add an underscore
        - no special characters
        """
        if value is not None:
            try:
                return validate_json(value)
            except ValueError:
                raise ValueError('tags needs to be a valid JSON')
        return value

    @validates('input_min')
    def validate_input_min(self, _, value):
        if value is not None and self.input_max is not None and value > self.input_max:
            raise ValueError("input_min cannot be greater than input_max")
        return value

    @validates('input_max')
    def validate_input_max(self, _, value):
        if self.input_min is not None and value is not None and self.input_min > value:
            raise ValueError("input_min cannot be greater than input_max")
        return value

    @validates('scale_min')
    def validate_scale_min(self, _, value):
        if value is not None and self.scale_max is not None and value > self.scale_max:
            raise ValueError("scale_min cannot be greater than scale_max")
        return value

    @validates('scale_max')
    def validate_scale_max(self, _, value):
        if self.scale_min is not None and value is not None and self.scale_min > value:
            raise ValueError("scale_min cannot be greater than scale_max")
        return value

    @validates('function_code')
    def validate_function_code(self, _, value):
        if isinstance(value, ModbusFunctionCode):
            function_code: ModbusFunctionCode = value
        elif isinstance(value, int):
            try:
                function_code: ModbusFunctionCode = ModbusFunctionCode(value)
            except Exception:
                raise ValueError("Invalid function code")
        else:
            if not value or value not in ModbusFunctionCode.__members__:
                raise ValueError("Invalid function code")
            function_code: ModbusFunctionCode = ModbusFunctionCode[value]
        return function_code

    @validates('register')
    def validate_register(self, _, value):
        if value < 0 or value > 65535:
            raise ValueError('Invalid register')
        return value

    @validates('register_length')
    def validate_register_length(self, _, value):
        if value < 0 or value > 65535:
            raise ValueError('Invalid register length')
        return value

    @validates('data_type')
    def validate_data_type(self, _, value):
        if isinstance(value, ModbusDataType):
            return value
        if not value or value not in ModbusDataType.__members__:
            raise ValueError("Invalid data type")
        return ModbusDataType[value]

    @validates('data_endian')
    def validate_data_endian(self, _, value):
        if isinstance(value, ModbusDataEndian):
            return value
        if not value or value not in ModbusDataEndian.__members__:
            raise ValueError("Invalid data endian")
        return ModbusDataEndian[value]

    def update_point_value(self, point_store: PointStoreModel, cov_threshold: float = None) -> bool:
        if not point_store.fault:
            if cov_threshold is None:
                cov_threshold = self.cov_threshold

            value = point_store.value_original
            if value is not None:
                value = self.apply_scale(value, self.input_min, self.input_max, self.scale_min,
                                         self.scale_max)
                value = self.apply_value_operation(value, self.value_operation)
                value = round(value, self.value_round)
            point_store.value = self.apply_point_type(value)
        return point_store.update(cov_threshold)

    def save_to_db(self):
        self.point_store = PointStoreModel.create_new_point_store_model(self.uuid)
        super().save_to_db()

    def check_self(self) -> (bool, any):
        super().check_self()

        reg_length = self.register_length
        point_fc: ModbusFunctionCode = self.function_code
        if self.is_writable(point_fc):
            self.writable = True
            if not self.priority_array_write:
                self.priority_array_write = PriorityArrayModel(_16=self.fallback_value)
            if reg_length > 1 and point_fc == ModbusFunctionCode.WRITE_COIL:
                self.function_code = ModbusFunctionCode.WRITE_COILS
            elif reg_length == 1 and point_fc == ModbusFunctionCode.WRITE_COILS:
                self.function_code = ModbusFunctionCode.WRITE_COIL
            elif reg_length > 1 and point_fc == ModbusFunctionCode.WRITE_REGISTER:
                self.function_code = ModbusFunctionCode.WRITE_REGISTERS
            elif reg_length == 1 and point_fc == ModbusFunctionCode.WRITE_REGISTERS:
                self.function_code = ModbusFunctionCode.WRITE_REGISTER
        else:
            self.writable = False
            if self.priority_array_write and self.priority_array_write.point_uuid:
                self.priority_array_write.delete_from_db()

        data_type = self.data_type
        if not isinstance(data_type, ModbusDataType):
            data_type = ModbusDataType[self.data_type]
        if point_fc == ModbusFunctionCode.READ_DISCRETE_INPUTS or point_fc == ModbusFunctionCode.READ_COILS or \
                point_fc == ModbusFunctionCode.WRITE_COIL:
            data_type = ModbusDataType.DIGITAL
            self.data_type = ModbusDataType.DIGITAL
            self.register_length = 1
            self.value_round = 0

        if data_type == ModbusDataType.FLOAT or data_type == ModbusDataType.INT32 or \
                data_type == ModbusDataType.UINT32:
            self.register_length = 2

        return True

    def apply_point_type(self, value: float) -> float:
        return value

    def _get_highest_priority_field(self):
        for i in range(1, 17):
            value = getattr(self.priority_array_write, f'_{i}', None)
            if value is not None:
                return i
        return 16

    def publish_cov(self, point_store: PointStoreModel, device=None, network: NetworkModel = None,
                    force_clear: bool = False):
        from src.models.model_device import DeviceModel
        if point_store is None:
            raise Exception('Point.publish_cov point_store cannot be None')
        if device is None:
            device = DeviceModel.find_by_uuid(self.device_uuid)
        if network is None:
            network = NetworkModel.find_by_uuid(device.network_uuid)
        if device is None or network is None:
            raise Exception(f'Cannot find network or device for point {self.uuid}')
        priority = self._get_highest_priority_field()
        from src.services.mqtt_client import MqttClient
        MqttClient.publish_point_cov(
            Drivers.MODBUS.name, network, device, self, point_store, force_clear, priority)

    def update(self, **kwargs) -> bool:
        changed: bool = super().update(**kwargs)
        updated: bool = self.update_point_value(self.point_store, 0)
        if updated:
            self.publish_cov(self.point_store)

        return changed

    def update_point_store(self, value: float, priority: int, priority_array_write: dict):
        self.update_priority_value(value, priority, priority_array_write)
        highest_priority_value: float = PriorityArrayModel.get_highest_priority_value(self.uuid)
        self.update_point_store_value(highest_priority_value)

    def update_point_store_value(self, highest_priority_value: float):
        point_store = PointStoreModel(point_uuid=self.uuid,
                                      value_original=highest_priority_value)
        updated = self.update_point_value(point_store)
        if updated:
            self.publish_cov(point_store)

    def update_priority_value(self, value: float, priority: int, priority_array_write: dict):
        if priority_array_write:
            priority_array: PriorityArrayModel = PriorityArrayModel.find_by_point_uuid(self.uuid)
            if priority_array:
                priority_array.update(**priority_array_write)
            return
        if not priority:
            priority = 16
        if priority not in range(1, 17):
            raise ValueError('priority should be in range(1, 17)')
        if priority:
            priority_array: PriorityArrayModel = PriorityArrayModel.find_by_point_uuid(self.uuid)
            if priority_array:
                priority_array.update(**{f"_{priority}": value})

    @classmethod
    def apply_value_operation(cls, original_value, value_operation: str) -> float or None:
        """Do calculations on original value with the help of point details"""
        if original_value is None or value_operation is None or not value_operation.strip():
            return original_value
        return eval_arithmetic_expression(value_operation.lower().replace('x', str(original_value)))

    @classmethod
    def apply_scale(cls, value: float, input_min: float, input_max: float, output_min: float, output_max: float) \
            -> float or None:
        if value is None or input_min is None or input_max is None or output_min is None or output_max is None:
            return value
        if input_min == input_max or output_min == output_max:
            return value
        scaled = ((value - input_min) / (input_max - input_min)) * (output_max - output_min) + output_min
        if scaled > max(output_max, output_min):
            return max(output_max, output_min)
        elif scaled < min(output_max, output_min):
            return min(output_max, output_min)
        else:
            return scaled

    @classmethod
    def revert_scale(cls, scaled: float, input_min: float, input_max: float, output_min: float, output_max: float) \
            -> float or None:
        if scaled is None or input_min is None or input_max is None or output_min is None or output_max is None:
            return scaled
        if input_min == input_max or output_min == output_max:
            return scaled
        if scaled > max(output_max, output_min):
            scaled = max(output_max, output_min)
        elif scaled < min(output_max, output_min):
            scaled = min(output_max, output_min)
        value = ((scaled - output_min) * (input_max - input_min)) / (output_max - output_min) + input_min
        return value

    @classmethod
    def filter_by_device_uuid(cls, device_uuid: str):
        return cls.query.filter_by(device_uuid=device_uuid)

    @classmethod
    def create_temporary_from_string(cls, string: str):
        split_string = string.split(':')
        if len(split_string) != 3:
            raise ValueError('Invalid Modbus Point string format ("<FC>:<Register>:<Length>')
        data = {
            'function_code': int(split_string[0]),
            'register': int(split_string[1]),
            'register_length': int(split_string[2]),
        }
        point = cls.create_temporary(**data)
        point.validate_function_code(None, point.function_code)
        point.validate_register(None, point.register)
        point.validate_register_length(None, point.register_length)
        return point

    @classmethod
    def find_by_name(cls, network_name: str, device_name: str, point_name: str):
        from src.models.model_device import DeviceModel
        results = cls.query.filter_by(name=point_name) \
            .join(DeviceModel).filter_by(name=device_name) \
            .join(NetworkModel).filter_by(name=network_name) \
            .first()
        return results

    @staticmethod
    def is_writable(value: ModbusFunctionCode) -> bool:
        return value in [ModbusFunctionCode.WRITE_COIL, ModbusFunctionCode.WRITE_COILS,
                         ModbusFunctionCode.WRITE_REGISTER, ModbusFunctionCode.WRITE_REGISTERS]

    @staticmethod
    def is_writable_by_str(value: str) -> bool:
        return value in [ModbusFunctionCode.WRITE_COIL.name, ModbusFunctionCode.WRITE_COILS.name,
                         ModbusFunctionCode.WRITE_REGISTER.name, ModbusFunctionCode.WRITE_REGISTERS.name]

    def get_highest_priority_write_value(self):
        highest_priority_value = get_highest_priority_value_from_priority_array(self.priority_array_write)
        if not highest_priority_value:
            return None
        if self.function_code in (ModbusFunctionCode.WRITE_COIL, ModbusFunctionCode.WRITE_COILS,
                                  ModbusFunctionCode.WRITE_REGISTER, ModbusFunctionCode.WRITE_REGISTERS):
            equation = f'{self.value_operation}={highest_priority_value}'
            highest_priority_value = eval_arithmetic_equation(equation)
            highest_priority_value = self.revert_scale(highest_priority_value, self.input_min, self.input_max,
                                                       self.scale_min, self.scale_max)
        return round(highest_priority_value, self.value_round)
