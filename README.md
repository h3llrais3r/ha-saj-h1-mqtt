# SAJ H1 solar inverter (MQTT)

Home Assistant integration for SAJ H1 solar inverters. \
This custom integration provides MQTT integration for SAJ H1 solar inverters. \
**DISCLAIMER:** I won't be responsible for any kind of loss during it usage, the integration is provided AS-IS.

## Configure Home Assistant MQTT broker

This integration uses the MQTT services already configured in Home Assistant to communicate with the inverter and retrieve the data. \
For this reason you need to first setup a broker and configure Home Assistant to talk to using the standard MQTT integration. \
Of course, if you already have MQTT configured, you don't need to do this again.

## Configure the inverter

The last step is to configure the inverter (actually the Wifi communication module AIO3 attached to the inverter) to talk with the local MQTT broker and not directly with the SAJ broker. \
To do that, you have 3 options:
- Change the MQTT broker using the SAJ [eSolar O&M](https://play.google.com/store/apps/details?id=com.saj.operation) app to your local MQTT broker.
- Poison your local DNS to redirect the MQTT messages to your broker. This consists in telling your home router to point to your broker IP when domain **mqtt.saj-solar.com** is queried by the inverter. Refer to your router capabilities to handle this. This may require some time for the inverter to discover that the broker IP changed, so you may want to remove and reinstall the Wifi AIO3 module to restart it.
- Setup a bridge on your local MQTT broker to the SAJ mqtt broker if you still want to use the SAJ [Home](https://play.google.com/store/apps/details?id=com.saj.home) app. For instructions, see [here](https://github.com/paolosabatino/saj-mqtt-ha/discussions/4).

## Install the integration

### Option 1: via HACS

- Add a custom integration repository to HACS: https://github.com/h3llrais3r/ha-saj-h1-mqtt
- Once the repository is added, use the search bar and type "SAJ H1 solar inverter (MQTT)"
- Download the integration by using the `Download` button
- Restart Home Assistant
- Setup the integration as described below (see: Setting up the integration)

### Option 2: manual installation

- In the `custom_components` directory of your home assistant system create a directory called `saj_h1_mqtt`.
- Download all the files from `/custom_components/saj_h1_mqtt/` directory in this repository and place them in the `saj_h1_mqtt` directory you created before.
- Restart Home Assistant
- Setup the integration as described below (see: Setting up the integration)

## Setting up the integration

- Go to Configuration -> Integrations and add "SAJ H1 solar inverter (MQTT)" integration
- Provide the serial number of your inverter
- Specify the realtime data scan interval
- Optionally, if you would have multiple inverters, you can include the serial number in the sensor sames
- Click submit to enable the integration
- Optionally, you can configure the integration again to:
    - include additional data:
        - inverter data
        - battery data
        - battery controller data
        - config data
    - enable accurate realtime power data (as SAJ tries to hide minimal grid import/export from the realtime data)
    - enable mqqt debugging (for debugging purposes)

## HA services

This integration also exposes a few services that can be used from within home assistant.
The following services are available:
- `saj_h1_mqtt.read_register`, to read a value of any register
- `saj_h1_mqtt.write_register`, to write to any value to any register (USE AT OWN RISK AS THIS CAN DAMAGE YOUR INVERTER!)
- `saj_h1_mqtt.refresh_inverter_data`, to refresh the inverter data sensors
- `saj_h1_mqtt.refresh_battery_data`, to refresh teh battery data sensors
- `saj_h1_mqtt.refresh_battery_controller_data`, to refresh teh battery controller data sensors
- `saj_h1_mqtt.refresh_config_data`, to refresh the config data sensors