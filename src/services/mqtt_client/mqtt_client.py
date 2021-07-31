import json
import logging
from typing import Callable, List, Union

from registry.models.model_device_info import DeviceInfoModel
from registry.resources.resource_device_info import get_device_info

from src.models.model_point import PointModel
from src.models.model_point_store import PointStoreModel
from src.services.event_service_base import EventServiceBase, Event, EventType
from src.services.mqtt_client.mqtt_listener import MqttListener
from .mqtt_registry import MqttRegistry
from ...setting import MqttSetting

logger = logging.getLogger(__name__)

SERVICE_NAME_MQTT_CLIENT = 'mqtt'

MQTT_TOPIC_COV = 'cov'
MQTT_TOPIC_COV_ALL = 'all'
MQTT_TOPIC_COV_VALUE = 'value'


def allow_only_on_prefix(func):
    def inner_function(*args, **kwargs):
        prefix_topic: str = MqttClient.prefix_topic()
        if not prefix_topic:
            return
        func(*args, **kwargs)

    return inner_function


class MqttClient(MqttListener, EventServiceBase):

    def __init__(self):
        MqttListener.__init__(self)
        EventServiceBase.__init__(self, SERVICE_NAME_MQTT_CLIENT, False)
        self.supported_events[EventType.POINT_COV] = True
        self.supported_events[EventType.MQTT_DEBUG] = True

    @property
    def config(self) -> MqttSetting:
        return super().config if isinstance(super().config, MqttSetting) else MqttSetting()

    @allow_only_on_prefix
    def start(self, config: MqttSetting, subscribe_topics: List[str] = None, callback: Callable = lambda: None):
        from src.event_dispatcher import EventDispatcher
        EventDispatcher().add_service(self)
        MqttRegistry().add(self)
        super().start(config, subscribe_topics, callback)

    def _publish_cov(self, driver_name, network_uuid: str, network_name: str, device_uuid: str, device_name: str,
                     point: PointModel, point_store: PointStoreModel, clear_value: bool, priority: int):
        if point is None or device_uuid is None or network_uuid is None or driver_name is None \
                or network_name is None or device_name is None:
            raise Exception('Invalid MQTT publish arguments')

        payload: str = ''
        if not clear_value:
            output: dict = {
                'fault': point_store.fault,
                'value': point_store.value,
                'value_raw': point_store.value_raw,
                'ts': str(point_store.ts_value),
                'priority': priority
            }
            if point_store.fault:
                output = {**output, 'fault_message': point_store.fault_message, 'ts': str(point_store.ts_fault)}
            payload = json.dumps(output)

        if self.config.publish_value:
            topic: str = self.__make_topic((self.config.topic, MQTT_TOPIC_COV, MQTT_TOPIC_COV_ALL, driver_name,
                                            network_uuid, network_name,
                                            device_uuid, device_name,
                                            point.uuid, point.name))
            self._publish_mqtt_value(topic, payload)

            if not point_store.fault:
                topic: str = self.__make_topic((self.config.topic, MQTT_TOPIC_COV, MQTT_TOPIC_COV_VALUE, driver_name,
                                                network_uuid, network_name,
                                                device_uuid, device_name,
                                                point.uuid, point.name))
                self._publish_mqtt_value(topic, '' if clear_value else str(point_store.value))

    @allow_only_on_prefix
    def _run_event(self, event: Event):
        if event.data is None:
            return
        if event.event_type == EventType.MQTT_DEBUG and self.config.publish_debug:
            self._publish_mqtt_value(self.__make_topic((self.config.debug_topic,)), event.data, False)

        elif event.event_type == EventType.POINT_COV:
            self._publish_cov(event.data.get('driver_name'),
                              event.data.get('network').uuid, event.data.get('network').name,
                              event.data.get('device').uuid, event.data.get('device').name,
                              event.data.get('point'), event.data.get('point_store'),
                              event.data.get('clear_value'),
                              event.data.get('priority'))

    def _publish_mqtt_value(self, topic: str, payload: str, retain: bool = True):
        if not self.status():
            logger.error(f"MQTT client {self.to_string()} is not connected...")
            return
        logger.debug(f"MQTT_PUBLISH: 'topic': {topic}, 'payload': {payload}, 'retain':{retain}")
        self.client.publish(topic, str(payload), qos=self.config.qos, retain=retain)

    @classmethod
    def prefix_topic(cls) -> str:
        device_info: Union[DeviceInfoModel, None] = get_device_info()
        if not device_info:
            logger.error('Please add device_info on Rubix Service')
            return ''
        return cls.SEPARATOR.join((device_info.client_id, device_info.client_name,
                                   device_info.site_id, device_info.site_name,
                                   device_info.device_id, device_info.device_name))

    @classmethod
    def __make_topic(cls, parts: tuple) -> str:
        return cls.SEPARATOR.join((cls.prefix_topic(),) + parts)