from flask_restful import marshal_with, reqparse
from rubix_http.exceptions.exception import NotFoundException

from src.models.model_point import PointModel
from src.resources.point.point_base import PointBaseResource
from src.resources.rest_schema.schema_point import point_all_fields, point_all_attributes
from src.models.model_priority_array import PriorityArrayModel


class PointSingularResource(PointBaseResource):
    """
    It returns point with point_store object value, which has the current values of point_store for that particular
    point with last not null value and value_raw
    """
    patch_parser = reqparse.RequestParser()
    for attr in point_all_attributes:
        patch_parser.add_argument(attr,
                                  type=point_all_attributes[attr]['type'],
                                  required=False,
                                  store_missing=False)

    @classmethod
    @marshal_with(point_all_fields)
    def get(cls, **kwargs):
        point: PointModel = cls.get_point(**kwargs)
        if not point:
            raise NotFoundException('Modbus Point not found')
        return point

    @classmethod
    @marshal_with(point_all_fields)
    def put(cls, **kwargs):
        data = cls.parser.parse_args()
        point: PointModel = cls.get_point(**kwargs)
        if not point:
            return cls.add_point(data)
        return cls.update_point(data, point)

    @classmethod
    def update_point(cls, data: dict, point: PointModel) -> PointModel:
        priority_array_write: dict = data.pop('priority_array_write') if data.get('priority_array_write') else {}
        highest_priority_value: float = PriorityArrayModel.get_highest_priority_value_from_priority_array(
            point.priority_array_write)
        if not priority_array_write and not highest_priority_value:
            priority_array_write = {'_16': data.get('fallback_value', None) or point.fallback_value}
        if priority_array_write:
            priority_array = PriorityArrayModel.find_by_point_uuid(point.uuid)
            if priority_array:
                priority_array.update(**priority_array_write)
        point.update(**data)
        return point

    @classmethod
    @marshal_with(point_all_fields)
    def patch(cls, **kwargs):
        data = cls.patch_parser.parse_args()
        point: PointModel = cls.get_point(**kwargs)
        if not point:
            raise NotFoundException('Modbus Point not found')
        return cls.update_point(data, point)

    @classmethod
    def delete(cls, **kwargs):
        point: PointModel = cls.get_point(**kwargs)
        point.publish_cov(point.point_store, force_clear=True)
        if not point:
            raise NotFoundException('Modbus Point not found')
        point.delete_from_db()
        return '', 204

    @classmethod
    def get_point(cls, **kwargs) -> PointModel:
        raise NotImplementedError


class PointSingularResourceByUUID(PointSingularResource):
    @classmethod
    def get_point(cls, **kwargs) -> PointModel:
        return PointModel.find_by_uuid(kwargs.get('uuid'))


class PointSingularResourceByName(PointSingularResource):
    @classmethod
    def get_point(cls, **kwargs) -> PointModel:
        return PointModel.find_by_name(kwargs.get('network_name'), kwargs.get('device_name'),
                                       kwargs.get('point_name'))
