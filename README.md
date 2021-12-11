# Home Assistant Helpers

[HomeAssistant](https://www.home-assistant.io/) related stuff. Scripts,
blueprints, automations, scenes, sensors, configs.

#### Description

The repository contains Python scripts and YAML configs one might find useful
for a HASS setup.

#### Pre-requisites

- Python programming experience
- understanding HomeAssistant
  [integrations](https://www.home-assistant.io/integrations/python_script/)
- admin access to HASS instance

## Python Scripts

### - alexa_tts.py

Plays a TTS message on Amazon Echo devices using Alexa notification service. A
list of target devices is generated based on time, recent motion activity, and a
set of default and last resort targets.

Usage:

From /config/automations.yaml

```yaml
action:
  - service: python_script.alexa_tts
    data:
      message: Garage door opened.
      silent_in:
        - garage
```

The alexa_tts.py depends on the set of sensors. You can customaze them based on
your needs and situation. Here are some examples:

From /config/binary_sensors.yaml

```yaml
platform: template
  sensors:
    is_quite_time:
      friendly_name: "Quite Time"
      value_template: "{% if (now().strftime('%-H') | int < 7) or (now().strftime('%-H') | int >= 22) %}on{% else %}off{% endif %}"

```

From /config/sensors.yaml

```yaml
platform: template
sensors:
  garage_last_5m_motion:
    friendly_name: "Motion in the Garage within Last 5 minutes"
    value_template:
      "{% if (as_timestamp(now()) | int -
      as_timestamp(states.group.garage_motion_sensors.last_changed) | int) < 300
      %}on{% else %}off{% endif %}"
```

from /config/groups.yaml

```yaml
garage_motion_sensors:
  name: Garage Motion Sensors
  entities:
    - binary_sensor.garage_motion_sensor_1_motion
    - binary_sensor.garage_motion_sensor_2_motion
    - binary_sensor.garage_motion_sensor_3_motion
```

from /config/configuration.yaml

```yaml
binary_sensor: !include binary_sensors.yaml
group: !include groups.yaml
python_script:
sensor: !include sensors.yaml
```

#### ENV

The script behaviour heavily depends on the quite/normal time sensor state. You
can also set default and last resor targets via ENV dictionary. The default
targets will remain active as long as they are not specifically silenced during
alexa_tts.py invocation using `slinet_in` parameter. The last resort targets
will be used if resulting targets list is empty.

```python
ENV = {
    "NORMAL_TIME_DEFAULT_TARGETS": {},
    "NORMAL_TIME_LAST_RESORT_TARGETS": {
        CORRIDOR: CORRIDOR_ECHO
    },
    "QUITE_TIME_DEFAULT_TARGETS": {
        BEDROOM_1: BEDROOM_1_ECHO
    },
}
```

#### RULES

Each area behaviour is configured in RULES.

- conditions: a set of conditions (sensor is on) to check for the targets
  activation
- target: the echo device
- unless: (don't play in the area if)
  - conditions: any of these is ON (or empty)
  - target: and this target (normaly from the nearest area) is playing

```python
RULES = (
    {
        "conditions": (BATHROOM_1_LIGHT, BATHROOM_1_MOTION),
        "target": BATHROOM_1_ECHO,
        "unless": {
            "conditions": (BATHROOM_1_DOOR,),
            "target": BEDROOM_1_ECHO
        }
    },
    {
        "conditions": (GARAGE_LIGHT, GARAGE_MOTION),
        "target": GARAGE_ECHO
    },
    {
        "conditions": (OFFICE_1_LIGHT, OFFICE_1_MOTION, OFFICE_1_TV),
        "target": OFFICE_1_ECHO
    },
)
```

### - alexa_volume.py

Sets the volume level on Amazon Echo devices.

#### DEVICES

A list of media player device IDs to control with alexa_volume.py

```python
DEVICES = (
    "bathroom_1_echo",
    "bathroom_2_echo"
    "bedroom_1_echo"
    "corridor_echo",
    "garage_echo",
    "living_room_echo",
    "office_1_echo",
    "office_2_echo",
)
```

## Blueprints

### - idle_target_turn_off.yaml

The automation periodically checks the target area and loads a specific scene to
turn off the target if no activity has been detected for a specified amount of
time.

### - scenes_automation.yaml

Automates Scenes Activation.

The automation supports two default scenes for 'on'/'off' `Watcher` states and
three optional scenes which are activated depending on the current time.

### - tts_state.yaml

Plays TTS message upon entity state change event.

The automation uses
[alexa_tts.py](https://github.com/arkid15r/hass/blob/main/python_scripts/alexa_tts.py)
to play the TTS message.
