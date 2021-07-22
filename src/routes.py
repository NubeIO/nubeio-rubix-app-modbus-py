from flask import Blueprint
from flask_restful import Api

from src.system.resources.ping import Ping
from src.models.model_network import NetworkModel
from src.models.model_priority_array import PriorityArrayModel
from src.models.model_device import DeviceModel
from src.models.model_point import PointModel
from src.models.model_priority_array import PriorityArrayModel
from src.models.model_point_store import PointStoreModel

bp_system = Blueprint('system', __name__, url_prefix='/api/system')
Api(bp_system).add_resource(Ping, '/ping')
