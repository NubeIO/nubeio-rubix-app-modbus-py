from flask_restful import marshal_with

from src.models.point.point import PointModel
from src.resources.point.point_base import PointBaseResource
from src.resources.rest_schema.schema_point import point_all_fields


class PointPluralResource(PointBaseResource):
    @classmethod
    @marshal_with(point_all_fields)
    def get(cls):
        return PointModel.find_all()

    @classmethod
    @marshal_with(point_all_fields)
    def post(cls):
        data = PointPluralResource.parser.parse_args()
        return cls.add_point(data)
