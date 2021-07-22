from rubix_http.exceptions.exception import NotFoundException
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import validates

from src import db
from src.enums.network import ModbusType
from src.models.point.point import PointModel
from src.models.network.network import NetworkModel

from src.models.model_base import ModelBase


class DeviceModel(ModelBase):
    __tablename__ = 'devices'
    uuid = db.Column(db.String(80), primary_key=True, nullable=False)
    network_uuid = db.Column(db.String, db.ForeignKey('networks.uuid'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    enable = db.Column(db.Boolean(), nullable=False)
    fault = db.Column(db.Boolean(), nullable=True)
    tags = db.Column(db.String(320), nullable=True)
    type = db.Column(db.Enum(ModbusType), nullable=False)
    address = db.Column(db.Integer(), nullable=False)
    zero_based = db.Column(db.Boolean(), nullable=False, default=False)
    ping_point = db.Column(db.String(10))
    supports_multiple_rw = db.Column(db.Boolean(), nullable=False, default=False)
    network_uuid_constraint = db.Column(db.String, nullable=False)
    points = db.relationship('PointModel', cascade="all,delete", backref='device', lazy=True)

    __table_args__ = (
        UniqueConstraint('address', 'network_uuid_constraint'),
    )

    @validates('ping_point')
    def validate_ping_point(self, _, value):
        if value is None:
            return value
        PointModel.create_temporary_from_string(value)
        return value

    def check_self(self) -> (bool, any):
        super().check_self()
        if self.network_uuid is None:  # for temporary models
            return True
        network = NetworkModel.find_by_uuid(self.network_uuid)
        # can't get sqlalchemy column default to do this so this is solution
        if network is None:
            raise NotFoundException(f'No network found with uuid {self.network_uuid}')
        self.type = network.type
        self.network_uuid_constraint = self.network_uuid
        return True
