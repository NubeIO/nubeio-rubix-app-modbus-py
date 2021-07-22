from typing import List

from src.models.point.point import PointModel
from src.resources.point.point_base import PointBaseResource
from src.models.point.point_store import PointStoreModel


# TODO: move all to base point_store resource
# TODO: use @marshal_with
class PointPluralPointStoreResource(PointBaseResource):
    @classmethod
    def get(cls):
        points: List[PointModel] = PointModel.find_all()
        serialized_output = {}
        for point in points:
            if point.device_uuid not in serialized_output:
                serialized_output[point.device_uuid] = []
            serialized_output[point.device_uuid].append(get_point_store(point, point.point_store))
        return serialized_output


class PointStoreResource(PointBaseResource):
    @classmethod
    def get(cls, uuid):
        point_store: PointStoreModel = PointStoreModel.find_by_point_uuid(uuid)
        if point_store is None:
            return {}
        else:
            point: PointModel = PointModel.find_by_uuid(uuid)
            return get_point_store(point, point_store)


class DevicePointPluralPointStoreResource(PointBaseResource):
    @classmethod
    def get(cls, device_uuid):
        points: List[PointModel] = PointModel.filter_by_device_uuid(device_uuid)
        serialized_output = []
        for point in points:
            serialized_output.append(get_point_store(point, point.point_store))
        return serialized_output


def get_point_store(point: PointModel, point_store: PointStoreModel) -> dict:
    return {
        'uuid': point.uuid,
        'name': point.name,
        'register': point.register,
        'fault': point_store.fault,
        'value': point_store.value
    }
