# Home Assistant Configuration

[Home Assistant](https://www.home-assistant.io/) scripts,
blueprints, automations, scenes, sensors, configs.

#### Description

The repository contains Python scripts and YAML configs one might find useful
for their Home Assistant setup.

## App Daemon Scripts

### - tts.py

Plays a TTS message on Amazon Echo devices using Alexa notification service.
A list of target devices is generated based on time, recent motion activity,
and a set of default and last resort targets.

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
        {{ now().strftime('%p') | lower == 'am' }}
```

From /config/includes/templates/motion.yaml

```yaml
- binary_sensor:
    - name: Bedroom 1 Motion
      unique_id: bedroom_1_motion
      state: >
        {{ is_state('binary_sensor.bedroom_1_motion_group', 'on') }}

    - name: Bedroom 1 Motion 15m
      unique_id: bedroom_1_motion_15m
      state: >
        {{ as_timestamp(now()) - as_timestamp(
            states.binary_sensor.bedroom_1_motion_group.last_changed) < 900
        }}

    - name: Bedroom 1 Motion 5m
      unique_id: bedroom_1_motion_5m
      state: >
        {{ as_timestamp(now()) - as_timestamp(
            states.binary_sensor.bedroom_1_motion_group.last_changed) < 300
        }}
```

from /config/includes/binary_sensors/motion.yaml

```yaml
- name: Front Yard Motion Group
  device_class: motion
  platform: group
  unique_id: front_yard_motion_group
  entities:
    - binary_sensor.doorbell_motion
    - binary_sensor.front_yard_camera_1_motion
    - binary_sensor.front_yard_camera_2_motion

- name: Garage Motion Group
  device_class: motion
  platform: group
  unique_id: garage_motion_group
  entities:
    - binary_sensor.garage_motion_sensor_1_motion
    - binary_sensor.garage_motion_sensor_2_motion
    - binary_sensor.garage_motion_sensor_3_motion
```

from /config/configuration.yaml

```yaml
binary_sensor: !include_dir_merge_list includes/binary_sensors
group: !include includes/groups.yaml
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
  play_always:
    normal_time: []
    quite_time:
      - bedroom_1
  play_default:
    normal_time:
      - corridor
    quite_time: []
quite_time: binary_sensor.quite_time
rules:
  bathroom_1:
    if_not:
      conditions:
        - binary_sensor.bathroom_1_door
      target: media_player.bedroom_1_echo
    conditions:
      - binary_sensor.bathroom_1_lights
      - binary_sensor.bathroom_1_motion_5m
    target: media_player.bathroom_1_echo
  bathroom_2:
    if_not:
      conditions:
        - binary_sensor.bathroom_2_door
      target: media_player.living_room_echo
    conditions:
      - binary_sensor.bathroom_2_lights
      - binary_sensor.bathroom_2_motion_5m
    target: media_player.bathroom_2_echo
  garage:
    conditions:
      - binary_sensor.garage_lights
      - binary_sensor.garage_motion_5m
    target: media_player.garage_echo
```

### - mp_volume.py

Sets the volume level on Amazon Echo devices.

#### AREAS

A list of media player device IDs to control with alexa_volume.py

```python
AREAS = (
    "bathroom_1",
    "bathroom_2"
    "bedroom_1"
    "garage",
    "living_room",
)
```

## Blueprints

### - target_turn_off.yaml

The automation periodically checks the target area and loads a specific scene to
turn off the target if no activity has been detected for a specified amount of
time.

### - scene_automation.yaml

Automates Scene Activation.

The automation supports two default scenes for 'on'/'off' `Watcher` states and
three optional scenes which are activated depending on the current time.

### - tts_state.yaml

Plays TTS message upon entity state change event.

The automation uses
[tts.py](https://github.com/arkid15r/home-assistant-config/blob/main/appdaemon/apps/tts.py)
to play TTS messages.

### - wake_up_lighting.yaml

Imitates sunrise lighting using a light device with brightness and color
temperature control capability.
