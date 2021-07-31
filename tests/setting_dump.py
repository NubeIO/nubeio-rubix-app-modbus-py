from src import AppSetting

if __name__ == '__main__':
    setting = '''
    {
      "drivers": {
        "modbus_rtu": false,
        "modbus_tcp": false
      },
      "services": {
        "mqtt": true
      },
      "mqtt": [
        {
          "enabled": true,
          "name": "rubix_points",
          "host": "0.0.0.0",
          "port": 1883,
          "keepalive": 60,
          "qos": 1,
          "attempt_reconnect_on_unavailable": true,
          "attempt_reconnect_secs": 5,
          "publish_value": true,
          "topic": "rubix/points"
        }
      ]
    }
    '''
    app_setting = AppSetting().reload(setting, is_json_str=True)
    print(type(app_setting.mqtt_settings))
    print(type(app_setting.services))
    print(type(app_setting.services.mqtt))
    print('-' * 30)
    assert len(app_setting.mqtt_settings) == 1
    print(app_setting.serialize())
    print('=' * 30)
    print('Default')
    print(AppSetting().serialize())
