# Home Assistant Configuration

[HomeAssistant](https://www.home-assistant.io/) related stuff. Scripts,
blueprints, automations, scenes, sensors, configs.

#### Description

The repository contains Python scripts and YAML configs one might find useful
for a HASS setup.

## Python Scripts

### - tts.py

Plays a TTS message on Amazon Echo devices using Alexa notification service. A
list of target devices can be configured based on time, recent motion activity,
and other binary sensors or templates with 'on'/'off' state capabilities.

Usage:

From /config/automations.yaml

```yaml
- event: tts
    event_data:
      text: Garage gate opened.
      areas_off:
        - garage
```

The tts.py depends on the set of sensors. You can customize them based on
your needs and situation. Here are some examples:

From /config/includes/binary_sensors.yaml

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
binary_sensor: !include includes/binary_sensors.yaml
group: !include_dir_merge_named includes/groups
template: !include_dir_merge_list includes/templates
```

#### ENV

The script behavior heavily depends on the quite/normal time sensor state. You
can set `play_always` and `play_default` targets. The play_always
targets will remain active as long as they are not explicitly silenced with
`areas_off` parameter during tts() function invocation. The play_default targets
will be used as a last resort when resulting target list is empty. Additional
targets can be added using areas_on parameter. Both areas_off/areas_on support
wildcard target value "\*" which expands to all targets found in apps.yaml
configuration file.

```yaml
env:
  play_always:
    normal_time: []
    quite_time:
      - bedroom_1
  play_default:
    normal_time:
      - corridor
    quite_time: []
```

#### RULES

Each area behavior is configured in AppDaemon apps.yaml.

- conditions: a set of conditions to check for the targets activation
- target: the echo device identifier
- if_not: (don't play in the area if)
  - conditions: any of these is ON (or empty)
  - target: and this target (normally from the nearest area) is playing

```yaml
env:
  quite_time: binary_sensor.quite_time
  rules:
    bathroom_1:
      conditions:
        - binary_sensor.motion_bathroom_1_5m
        - group.light_bathroom_1
      target: media_player.bathroom_1_echo
      if_not:
        conditions:
          - binary_sensor.bathroom_1_door
        target: media_player.bedroom_1_echo
    bathroom_2:
      conditions:
        - binary_sensor.motion_bathroom_2_5m
        - group.light_bathroom_2
      target: media_player.bathroom_2_echo
      if_not:
        conditions:
          - binary_sensor.bathroom_2_door
        target: media_player.living_room_echo
    garage:
      conditions:
        - binary_sensor.motion_garage_5m
        - group.light_garage
      target: media_player.garage_echo
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
