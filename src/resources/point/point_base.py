import shortuuid
from flask_restful import reqparse
from rubix_http.resource import RubixResource

from src.models.point.point import PointModel
from src.resources.rest_schema.schema_point import point_all_attributes, add_nested_priority_array_write
from src.models.point.priority_array import PriorityArrayModel


class PointBaseResource(RubixResource):
    parser = reqparse.RequestParser()
    for attr in point_all_attributes:
        parser.add_argument(attr,
                            type=point_all_attributes[attr]['type'],
                            required=point_all_attributes[attr].get('required', False),
                            help=point_all_attributes[attr].get('help', None),
                            store_missing=False)
    add_nested_priority_array_write()

    @classmethod
    def add_point(cls, data):
        uuid: str = shortuuid.uuid()
        priority_array_write: dict = data.pop('priority_array_write', {})
        paw = None
        if PointModel.is_writable_by_str(data.function_code):
            paw = PriorityArrayModel.create_priority_array_model(
                uuid,
                priority_array_write,
                data.get('fallback_value'))
        point = PointModel(
            uuid=uuid,
            priority_array_write=paw,
            **data
        )
        point.save_to_db()
        point.publish_cov(point.point_store)
        return point
