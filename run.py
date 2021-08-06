#!/usr/bin/env python3

import os

import click

from src import AppSetting, GunicornFlaskApplication
from src.utils.file import is_dir_exist, copy_point_server_database

CLI_CTX_SETTINGS = dict(help_option_names=["-h", "--help"], max_content_width=120, ignore_unknown_options=True,
                        allow_extra_args=True)


@click.command(context_settings=CLI_CTX_SETTINGS)
@click.option('-p', '--port', type=int, default=AppSetting.PORT, show_default=True, help='Port')
@click.option('-g', '--global-dir', type=click.Path(), help='Global dir',
              default=lambda: os.environ.get(AppSetting.GLOBAL_DIR_ENV))
@click.option('-d', '--data-dir', type=click.Path(), help='Application data dir',
              default=lambda: os.environ.get(AppSetting.DATA_DIR_ENV))
@click.option('-c', '--config-dir', type=click.Path(), help='Application config dir',
              default=lambda: os.environ.get(AppSetting.CONFIG_DIR_ENV))
@click.option('--prod', is_flag=True, help='Production mode')
@click.option('-s', '--setting-file', help='Setting json file', default=AppSetting.default_setting_file)
@click.option('-l', '--logging-conf', help='Logging config file')
@click.option('--gunicorn-config', help='Gunicorn: config file(gunicorn.conf.py)')
def cli(port, global_dir, data_dir, config_dir, prod, setting_file, logging_conf, gunicorn_config):
    setting = AppSetting(port=port, global_dir=global_dir, data_dir=data_dir, config_dir=config_dir,
                         prod=prod).reload(setting_file)
    if prod and not is_dir_exist(f'{setting.data_dir}/data.db'):
        copy_point_server_database(setting.data_dir)
    options = {
        'bind': '%s:%s' % ('0.0.0.0', setting.port),
        'workers': 1,
        'logconfig': logging_conf,
        'preload_app': False,
        'config': gunicorn_config
    }
    GunicornFlaskApplication(setting, options).run()


if __name__ == '__main__':
    cli()
