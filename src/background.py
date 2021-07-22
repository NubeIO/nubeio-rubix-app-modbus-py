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
        setting: AppSetting = current_app.config[AppSetting.FLASK_KEY]

    @staticmethod
    def sync_on_start():
        from rubix_http.request import gw_request
        from .models.point.point_store import PointStoreModel

        """Sync mapped points values from LoRa > Generic points values"""
        gw_request(api='/lora/api/sync/lp_to_gp')

        """Sync mapped points values from BACnet > Generic points values"""
        gw_request(api='/bacnet/api/sync/bp_to_gp')

        """Sync mapped points values from Modbus > Generic | BACnet points values"""
        PointStoreModel.sync_points_values_mp_to_gbp_process()
