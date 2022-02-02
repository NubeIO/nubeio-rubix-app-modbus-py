import re

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import validates

from src import db
from src.enums.network import ModbusType, ModbusRtuParity
from src.models.model_base import ModelBase
from src.utils.model_utils import validate_json


class NetworkModel(ModelBase):
    __tablename__ = 'networks'

    uuid = db.Column(db.String(80), primary_key=True, nullable=False)
    name = db.Column(db.String(80), nullable=False, unique=True)
    enable = db.Column(db.Boolean(), nullable=False)
    fault = db.Column(db.Boolean(), nullable=True)
    tags = db.Column(db.String(320), nullable=True)
    rtu_port = db.Column(db.String(80), nullable=True, unique=True)
    rtu_speed = db.Column(db.Integer(), default=9600)
    rtu_stop_bits = db.Column(db.Integer(), default=1)
    rtu_parity = db.Column(db.Enum(ModbusRtuParity), default=ModbusRtuParity.N)
    rtu_byte_size = db.Column(db.Integer(), default=8)
    tcp_ip = db.Column(db.String(80))
    tcp_port = db.Column(db.Integer())
    type = db.Column(db.Enum(ModbusType), nullable=False)
    timeout = db.Column(db.Integer(), nullable=False, default=3)
    polling_interval_runtime = db.Column(db.Integer(), default=2)
    point_interval_ms_between_points = db.Column(db.Integer(), default=30)
    devices = db.relationship('DeviceModel', cascade="all,delete", backref='network', lazy=True)

    __table_args__ = (
        UniqueConstraint('tcp_ip', 'tcp_port'),
    )

    def __repr__(self):
        return f"Network(uuid = {self.uuid})"

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

    @validates('name')
    def validate_name(self, _, value):
        if not re.match("^([A-Za-z0-9_-])+$", value):
            raise ValueError("name should be alphanumeric and can contain '_', '-'")
        return value

    @validates('type')
    def validate_type(self, _, value):
        if value == ModbusType.RTU.name:
            if not self.rtu_port:
                raise ValueError("rtu_port should be be there on type RTU")
            if self.rtu_byte_size is not None and self.rtu_byte_size not in range(5, 9):
                raise ValueError("rtu_byte_size The number of bits in a byte of serial data. This can be one of 5, 6, "
                                 "7, or 8. This defaults to 8")
        elif value == ModbusType.TCP.name:
            if not self.tcp_ip:
                raise ValueError("tcp_ip should be be there on type TCP")
            if not self.tcp_port:
                raise ValueError("tcp_port should be be there on type TCP")
        return ModbusType[value]

    @classmethod
    def find_by_name(cls, network_name: str):
        results = cls.query.filter_by(name=network_name).first()
        return results

    def set_fault(self, is_fault: bool):
        self.fault = is_fault
        db.session.commit()
