import os
import shutil
from logging import Logger
from pathlib import Path

from flask import current_app
from packaging import version
from werkzeug.local import LocalProxy

logger = LocalProxy(lambda: current_app.logger) or Logger(__name__)


def delete_existing_folder(dir_) -> bool:
    dir_path = Path(dir_)
    if dir_path.exists() and dir_path.is_dir():
        shutil.rmtree(dir_)
        return True
    return False


def is_dir_exist(dir_) -> bool:
    dir_path = Path(dir_)
    return dir_path.exists()


def get_extracted_dir(parent_dir) -> str:
    dir_path = Path(parent_dir)
    if dir_path.exists():
        dirs = os.listdir(parent_dir)
        if len(dirs):
            return os.path.join(parent_dir, dirs[0])
    return ""


def copy_point_server_database(data_dir: str):
    installed_version: str = get_extracted_dir('/data/rubix-service/apps/install/rubix-point-server')
    version_ = version.parse(installed_version.split("/")[-1])
    if installed_version and version.parse("v2.0.0") >= version_ >= version.parse("1.7.0") \
            and is_dir_exist('/data/point-server/data/data.db'):
        shutil.copyfile('/data/point-server/data/data.db', f'{data_dir}/data.db')
