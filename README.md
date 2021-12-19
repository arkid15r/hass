# Home Assistant Configuration

[HomeAssistant](https://www.home-assistant.io/) related stuff. Scripts,
blueprints, automations, scenes, sensors, configs.

#### Description

The repository contains Python scripts and YAML configs one might find useful
for a HASS setup.

## Python Scripts

### - tts.py

Plays a TTS message on Amazon Echo devices using Alexa notification service. A
list of target devices is generated based on time, recent motion activity, and a
set of default and last resort targets.

Usage:

From /config/automations.yaml

```yaml
- event: tts
    event_data:
      text: Garage gate opened.
      silent_in:
        - garage
```

The alexa_tts.py depends on the set of sensors. You can customaze them based on
your needs and situation. Here are some examples:

From /config/binary_sensors.yaml

```yaml
- binary_sensor:
    - unique_id: am
      name: AM
      icon: mdi:clock-time-twelve-outline
      state: >
        {{ now().strftime('%p')|lower == 'am' }}
```

From /config/includes/templates/motion.yaml

```yaml
- binary_sensor:
    - unique_id: motion_bathroom_1_15m
      name: Motion Bathroom 1 15m
      state: >
        {{ as_timestamp(now()) - as_timestamp(
             states.group.motion_bathroom_1.last_changed) < 900
        }}

    - unique_id: motion_bathroom_1_5m
      name: Motion Bathroom 1 5m
      state: >
        {{ as_timestamp(now()) - as_timestamp(
             states.group.motion_bathroom_1.last_changed) < 300
        }}
```

from /config/includes/groups/motion.yaml

```yaml
motion_front_yard:
  name: Front Yard Motion
  entities:
    - binary_sensor.doorbell_motion
    - binary_sensor.front_yard_camera_1_motion
    - binary_sensor.front_yard_camera_2_motion

motion_garage:
  name: Garage Motion
  entities:
    - binary_sensor.garage_motion_sensor_1_motion
    - binary_sensor.garage_motion_sensor_2_motion
    - binary_sensor.garage_motion_sensor_3_motion
```

from /config/configuration.yaml

```yaml
binary_sensor: !include binary_sensors.yaml
group: !include_dir_merge_named includes/groups
template: !include_dir_merge_list includes/templates
```

#### ENV

The script behavior heavily depends on the quite/normal time sensor state. You
can also set default and last resort targets via ENV dictionary. The default
targets will remain active as long as they are not specifically silenced during
tts.py invocation using `silent_in` parameter. The last resort targets
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

Each area behavior is configured in RULES.

- conditions: a set of conditions (sensor is on) to check for the targets
  activation
- target: the echo device
- unless: (don't play in the area if)
  - conditions: any of these is ON (or empty)
  - target: and this target (normally from the nearest area) is playing

```python
RULES = (
    {
        "conditions": (BEDROOM_1_LIGHT, BEDROOM_1_MOTION),
        "target": BEDROOM_1_ECHO
    },
    {
        "conditions": (GARAGE_LIGHT, GARAGE_MOTION),
        "target": GARAGE_ECHO
    },
    {
        "conditions": (
            DINING_AREA_LIGHT,
            HALLWAY_MOTION,
            KITCHEN_LIGHT,
            KITCHEN_MOTION,
            LIVING_ROOM_LIGHT,
            LIVING_ROOM_MOTION,
            LIVING_ROOM_TV,
        ),
        "target": LIVING_ROOM_ECHO
    },
    {
        "conditions": (OFFICE_1_LIGHT, OFFICE_1_MOTION, OFFICE_1_TV),
        "target": OFFICE_1_ECHO,
        "unless": {
            "conditions": (DINING_AREA_LIGHT, KITCHEN_LIGHT, KITCHEN_TV,
                            LIVING_ROOM_LIGHT, LIVING_ROOM_TV),
            "target": LIVING_ROOM_ECHO
        }
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
[tts.py](https://github.com/arkid15r/hass/blob/main/appdaemon/apps/tts.py)
to play the TTS message.
