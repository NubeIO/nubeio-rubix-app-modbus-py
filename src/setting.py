import json
import os
from typing import List

from flask import Flask
from rubix_mqtt.setting import MqttSettingBase


class BaseSetting:

    def reload(self, setting: dict):
        if setting is not None:
            self.__dict__ = {k: setting.get(k, v) for k, v in self.__dict__.items()}
        return self

    def serialize(self, pretty=True) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=2 if pretty else None)

    def to_dict(self):
        return json.loads(self.serialize(pretty=False))


class ServiceSetting(BaseSetting):
    """
    Declares an availability service(enabled/disabled option)
    """

    KEY = 'services'

    def __init__(self):
        self.mqtt = True


class DriverSetting(BaseSetting):
    """
    Declares an availability driver(enabled/disabled option)
    """

    KEY = 'drivers'

    def __init__(self):
        self.modbus_rtu: bool = True
        self.modbus_tcp: bool = False


class MqttSetting(MqttSettingBase):
    KEY = 'mqtt'

    def __init__(self):
        super(MqttSetting, self).__init__()
        self.cloud = False
        self.name = 'rubix-points'
        self.retain_clear_interval = 60
        self.publish_value = True
        self.topic = 'rubix/points/value'
        self.publish_debug = True
        self.debug_topic = 'rubix/points/debug'
        self.listen = True
        self.listen_topic = 'rubix/points/listen'


class AppSetting:
    PORT: int = 1516
    GLOBAL_DIR_ENV = 'APP_BASE_GLOBAL'
    DATA_DIR_ENV = 'APP_BASE_DATA'
    CONFIG_DIR_ENV = 'APP_BASE_CONFIG'
    KEY: str = 'APP_SETTING'
    default_global_dir = 'out'
    default_data_dir: str = 'data'
    default_config_dir: str = 'config'
    default_setting_file: str = 'config.json'
    default_logging_conf: str = 'logging.conf'
    fallback_logging_conf: str = 'config/logging.conf'
    fallback_logging_prod_conf: str = 'config/logging.prod.conf'

    def __init__(self, **kwargs):
        self.__port = kwargs.get('port') or AppSetting.PORT
        self.__global_dir = self.__compute_dir(kwargs.get('global_dir'), AppSetting.default_global_dir, 0o777)
        self.__data_dir = self.__compute_dir(self.__join_global_dir(kwargs.get('data_dir')),
                                             self.__join_global_dir(AppSetting.default_data_dir))
        self.__config_dir = self.__compute_dir(self.__join_global_dir(kwargs.get('config_dir')),
                                               self.__join_global_dir(AppSetting.default_config_dir))
        self.__prod = kwargs.get('prod') or False
        self.__driver_setting = DriverSetting()
        self.__service_setting = ServiceSetting()
        self.__mqtt_settings: List[MqttSetting] = [MqttSetting()]

    @property
    def port(self):
        return self.__port

    @property
    def global_dir(self):
        return self.__global_dir

    @property
    def data_dir(self):
        return self.__data_dir

    @property
    def config_dir(self):
        return self.__config_dir

    @property
    def prod(self) -> bool:
        return self.__prod

    @property
    def services(self) -> ServiceSetting:
        return self.__service_setting

    @property
    def drivers(self) -> DriverSetting:
        return self.__driver_setting

    @property
    def mqtt_settings(self) -> List[MqttSetting]:
        return self.__mqtt_settings

    def serialize(self, pretty=True) -> str:
        m = {
            DriverSetting.KEY: self.drivers,
            ServiceSetting.KEY: self.services,
            MqttSetting.KEY: [s.to_dict() for s in self.mqtt_settings],
            'prod': self.prod, 'global_dir': self.global_dir, 'data_dir': self.data_dir, 'config_dir': self.config_dir
        }
        return json.dumps(m, default=lambda o: o.to_dict() if isinstance(o, BaseSetting) else o.__dict__,
                          indent=2 if pretty else None)

    def reload(self, setting_file: str, is_json_str: bool = False):
        data = self.__read_file(setting_file, self.__config_dir, is_json_str)
        self.__driver_setting = self.__driver_setting.reload(data.get(DriverSetting.KEY))
        self.__service_setting = self.__service_setting.reload(data.get(ServiceSetting.KEY))
        mqtt_settings = data.get(MqttSetting.KEY, [])
        if len(mqtt_settings) > 0:
            self.__mqtt_settings = [MqttSetting().reload(s) for s in mqtt_settings]
        return self

    def init_app(self, app: Flask):
        app.config[AppSetting.KEY] = self
        return self

    def __join_global_dir(self, _dir):
        return _dir if _dir is None or _dir.strip() == '' else os.path.join(self.__global_dir, _dir)

    @staticmethod
    def __compute_dir(_dir: str, _def: str, mode=0o744) -> str:
        d = os.path.join(os.getcwd(), _def) if _dir is None or _dir.strip() == '' else _dir
        d = d if os.path.isabs(d) else os.path.join(os.getcwd(), d)
        os.makedirs(d, mode, True)
        return d

    @staticmethod
    def __read_file(setting_file: str, _dir: str, is_json_str=False):
        if is_json_str:
            return json.loads(setting_file)
        if setting_file is None or setting_file.strip() == '':
            return {}
        s = setting_file if os.path.isabs(setting_file) else os.path.join(_dir, setting_file)
        if not os.path.isfile(s) or not os.path.exists(s):
            return {}
        with open(s) as json_file:
            return json.load(json_file)
