"""
Plays a TTS message on Amazon Echo devices using Alexa notification service.
A list of target devices is generated based on time, recent motion activity,
and a set of default and last resort targets.

"""

#__author__ = "Ark (ark@cho.red)"

BATHROOM_1 = "bathroom_1"
BATHROOM_1_DOOR = "binary_sensor.bathroom_1_door"
BATHROOM_1_LIGHT = "group.light_bathroom_1"
BATHROOM_1_ECHO = "media_player.bathroom_1_echo"
BATHROOM_1_MOTION = "binary_sensor.motion_bathroom_1_5m"

BATHROOM_2 = "bathroom_2"
BATHROOM_2_DOOR = "binary_sensor.bathroom_2_door"
BATHROOM_2_LIGHT = "group.light_bathroom_2"
BATHROOM_2_ECHO = "media_player.bathroom_2_echo"
BATHROOM_2_MOTION = "binary_sensor.motion_bathroom_2_5m"

BEDROOM_1 = "bedroom_1"
BEDROOM_1_LIGHT = "group.light_bedroom_1"
BEDROOM_1_ECHO = "media_player.bedroom_1_echo"
BEDROOM_1_MOTION = "binary_sensor.motion_bedroom_1_5m"

CORRIDOR = "corridor"
CORRIDOR_ECHO = "media_player.corridor_echo"

DINING_AREA_LIGHT = "group.light_dining_area"

GARAGE = "garage"
GARAGE_LIGHT = "group.light_garage"
GARAGE_ECHO = "media_player.garage_echo"
GARAGE_MOTION = "binary_sensor.motion_garage_5m"

HALLWAY_MOTION = "group.hallway_motion_sensors"

KITCHEN_LIGHT = "group.light_kitchen"
KITCHEN_MOTION = "binary_sensor.motion_kitchen_5m"
KITCHEN_TV = "media_player.kitchen_tv"

LIVING_ROOM = "living_room"
LIVING_ROOM_LIGHT = "group.light_living_room"
LIVING_ROOM_ECHO = "media_player.living_room_echo"
LIVING_ROOM_MOTION = "binary_sensor.motion_living_room_5m"
LIVING_ROOM_TV = "binary_sensor.living_room_tv_powered_on"

OFFICE_1 = "office_1"
OFFICE_1_LIGHT = "group.light_office_1"
OFFICE_1_ECHO = "media_player.office_1_echo"
OFFICE_1_MOTION = "binary_sensor.motion_office_1_5m"
OFFICE_1_TV = "remote.office_1_tv_remote"

OFFICE_2 = "office_2"
OFFICE_2_LIGHT = "group.light_office_2"
OFFICE_2_ECHO = "media_player.office_2_echo"
OFFICE_2_MOTION = "binary_sensor.motion_office_2_5m"

QUITE_TIME = "binary_sensor.is_quite_time"

STATE_OFF = "off"
STATE_ON = "on"

ENV = {
    "NORMAL_TIME_DEFAULT_TARGETS": {},
    "NORMAL_TIME_LAST_RESORT_TARGETS": {
        CORRIDOR: CORRIDOR_ECHO
    },
    "QUITE_TIME_DEFAULT_TARGETS": {
        BEDROOM_1: BEDROOM_1_ECHO
    },
}

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
        "conditions": (BATHROOM_2_LIGHT, BATHROOM_2_MOTION),
        "target": BATHROOM_2_ECHO,
        "unless": {
            "conditions": (BATHROOM_2_DOOR,),
            "target": LIVING_ROOM_ECHO
        }
    },
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
    {
        "conditions": (OFFICE_2_LIGHT, OFFICE_2_MOTION),
        "target": OFFICE_2_ECHO
    },
)

TTS_DURATION_DEFAULT_SECONDS = 3
TTS_DURATION_TIMEOUT_SECONDS = 30
TTS_FLAG_IN_PROGRESS = 'input_boolean.tts_in_progress'


# pylint: disable=too-many-branches
def play(hass, message=None, silent_in=None, env=None):
  """
    Check targets and generate text to speach request.

    Parameters:
      hass: A HomeAssistant service from the global context.
      message: A text to play.
      silent_in: A list of areas to exclude.
      env: An environment settings for normal/quite time.

    Returns:
      list: A list of target devices the message to be played on.
    """

  def is_on(sensor):
    """
    	Returns True if sensor's state is "on" otherwise returns False.
    """

    return hass.states.get(sensor).state == STATE_ON

  if not message:
    raise ValueError("Message is required.")

  quite_hours = is_on(QUITE_TIME)

  targets = set()

  # Add targets based on the rule conditions.
  for rule in RULES:
    if any((is_on(c) for c in rule["conditions"])):
      targets.add(rule["target"])

  # Remove targets based on the unless condition.
  for rule in RULES:
    target = rule["target"]
    if (target not in targets or "unless" not in rule
        or rule["unless"]["target"] not in targets):
      continue

    conditions = rule["unless"]["conditions"]
    if not conditions:
      targets.remove(target)
    elif any((is_on(c) for c in conditions)):
      targets.remove(target)

  # Mute silenced targets.
  silenced_targets = {f"media_player.{area}_echo" for area in silent_in or ()}
  targets = targets.difference(silenced_targets)

  # Add default and last resort targets.
  if quite_hours:
    if "QUITE_TIME_DEFAULT_TARGETS" in env:
      targets.update(
          set(env["QUITE_TIME_DEFAULT_TARGETS"].values()).difference(
              silenced_targets))
  else:
    if "NORMAL_TIME_DEFAULT_TARGETS" in env:
      targets.update(
          set(env["NORMAL_TIME_DEFAULT_TARGETS"].values()).difference(
              silenced_targets))

    if not targets and "NORMAL_TIME_LAST_RESORT_TARGETS" in env:
      targets.update(
          set(env["NORMAL_TIME_LAST_RESORT_TARGETS"].values()).difference(
              silenced_targets))

  targets = list(targets)
  if targets:
    hass.services.call(
        "notify",
        "alexa_media",
        {
            "data": {
                "type": "tts",  # Text to speech.
            },
            "message": message,
            "target": targets,
        },
    )

  return targets


# pylint: disable=undefined-variable
def run(duration):
  """Acquire resource for `duration` time, run the function, and release the
     resource after completion.
  """

  def set_flag(flag, state):
    """Set flag state."""

    hass.services.call(
        "input_boolean",
        f"turn_{state}",
        {
            "entity_id": flag,
        },
    )

  # Acquire.
  set_flag(TTS_FLAG_IN_PROGRESS, state=STATE_ON)
  play(hass, data.get("message"), data.get("silent_in"), env=ENV)
  time.sleep(duration)

  # Release.
  set_flag(TTS_FLAG_IN_PROGRESS, state=STATE_OFF)


def wait(timeout):
  """Wait for another processes (if any) comtpletion."""

  wait_seconds = 0
  while (hass.states.get(TTS_FLAG_IN_PROGRESS) == STATE_ON
         and waited_seconds < timeout):
    time.sleep(1)
    wait_seconds += 1


wait(TTS_DURATION_TIMEOUT_SECONDS)
run(data.get("duration") or TTS_DURATION_DEFAULT_SECONDS)
