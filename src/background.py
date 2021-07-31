import logging
from threading import Thread

from flask import current_app

from .setting import AppSetting

logger = logging.getLogger(__name__)


class FlaskThread(Thread):
    """
    To make every new thread behinds Flask app context.
    Maybe using another lightweight solution but richer: APScheduler <https://github.com/agronholm/apscheduler>
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = current_app._get_current_object()

    def run(self):
        with self.app.app_context():
            super().run()


class Background:

    @staticmethod
    def run():
        setting: AppSetting = current_app.config[AppSetting.KEY]
        logger.info("Starting Drivers...")
        if setting.services.mqtt:
            from src.services.mqtt_client import MqttClient
            for config in setting.mqtt_settings:
                if not config.enabled:
                    continue
                mqtt_client = MqttClient()
                FlaskThread(target=mqtt_client.start, daemon=True, kwargs={'config': config}).start()
        if setting.drivers.modbus_tcp:
            from src.services.polling.modbus_polling import TcpPolling, ModbusTcpRegistry
            ModbusTcpRegistry().register()
            FlaskThread(target=TcpPolling().polling, daemon=True).start()

        if setting.drivers.modbus_rtu:
            from src.services.polling.modbus_polling import RtuPolling, ModbusRtuRegistry
            ModbusRtuRegistry().register()
            FlaskThread(target=RtuPolling().polling, daemon=True).start()

        # Sync
        logger.info("Starting Sync Services...")

        Background.sync_on_start()
        if setting.services.mqtt and any(config.enabled for config in setting.mqtt_settings):
            from .services.mqtt_republish import MqttRepublish
            FlaskThread(target=MqttRepublish().republish, daemon=True).start()

    @staticmethod
    def sync_on_start():
        from rubix_http.request import gw_request
        from src.models.model_point_store import PointStoreModel

        """Sync mapped points values from LoRa > Generic points values"""
        gw_request(api='/lora/api/sync/lp_to_gp')

        """Sync mapped points values from BACnet > Generic points values"""
        gw_request(api='/bacnet/api/sync/bp_to_gp')

        """Sync mapped points values from Modbus > Generic | BACnet points values"""
        PointStoreModel.sync_points_values_mp_to_gbp_process()