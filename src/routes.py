from flask import Blueprint
from flask_restful import Api

from src.resources.device.device_plural import DevicePluralResource
from src.resources.device.device_singular import DeviceSingularResourceByUUID, DeviceSingularResourceByName
from src.resources.network.netwrok_plural import NetworkPluralResource
from src.resources.network.netwrok_singular import NetworkSingularResourceByUUID, NetworkSingularResourceByName
from src.resources.point.point_plural import PointPluralResource
from src.resources.point.point_poll import PointPollResource, PointPollNonExistingResource
from src.resources.point.point_singular import PointSingularResourceByUUID, PointSingularResourceByName
from src.resources.point.point_stores import PointPluralPointStoreResource, PointStoreResource, \
    DevicePointPluralPointStoreResource
from src.resources.point.point_value_writer import PointUUIDValueWriterResource, PointNameValueWriterResource
from src.system.resources.ping import Ping

bp_system = Blueprint('system', __name__, url_prefix='/api/system')
Api(bp_system).add_resource(Ping, '/ping')

bp_modbus = Blueprint('modbus', __name__, url_prefix='/api/modbus')
api_modbus = Api(bp_modbus)
api_modbus.add_resource(NetworkPluralResource, '/networks')
api_modbus.add_resource(NetworkSingularResourceByUUID, '/networks/uuid/<string:uuid>')
api_modbus.add_resource(NetworkSingularResourceByName, '/networks/name/<string:name>')
api_modbus.add_resource(DevicePluralResource, '/devices')
api_modbus.add_resource(DeviceSingularResourceByUUID, '/devices/uuid/<string:uuid>')
api_modbus.add_resource(DeviceSingularResourceByName, '/devices/name/<string:network_name>/<string:device_name>')
api_modbus.add_resource(PointPluralResource, '/points')
api_modbus.add_resource(PointSingularResourceByUUID, '/points/uuid/<string:uuid>')
api_modbus.add_resource(PointSingularResourceByName,
                        '/points/name/<string:network_name>/<string:device_name>/<string:point_name>')
api_modbus.add_resource(PointPollResource, '/poll/point/<string:uuid>')
api_modbus.add_resource(PointPollNonExistingResource, '/poll/point')
api_modbus.add_resource(PointPluralPointStoreResource, '/point_stores')
api_modbus.add_resource(PointStoreResource, '/point_stores/<string:uuid>')
api_modbus.add_resource(DevicePointPluralPointStoreResource, '/<string:device_uuid>/point_stores')
api_modbus.add_resource(PointUUIDValueWriterResource, '/points_value/uuid/<string:uuid>')
api_modbus.add_resource(PointNameValueWriterResource,
                        '/points_value/name/<string:network_name>/<string:device_name>/<string:point_name>')
