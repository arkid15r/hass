"""
Plays a TTS message on Amazon Echo devices using Alexa notification service.
A list of target devices is generated based on time, recent motion activity,
and a set of default and last resort targets.

"""

__author__ = "Ark (ark@cho.red)"

BATHROOM_1 = "bathroom_1"
BATHROOM_1_DOOR = "binary_sensor.bathroom_1_door"
BATHROOM_1_LIGHT = "group.bathroom_1_bulbs"
BATHROOM_1_ECHO = "media_player.bathroom_1_echo"
BATHROOM_1_MOTION = "sensor.bathroom_1_last_5m_motion"

BATHROOM_2 = "bathroom_2"
BATHROOM_2_DOOR = "binary_sensor.bathroom_2_door"
BATHROOM_2_LIGHT = "group.bathroom_2_bulbs"
BATHROOM_2_ECHO = "media_player.bathroom_2_echo"
BATHROOM_2_MOTION = "sensor.bathroom_2_last_5m_motion"

BEDROOM_1 = "bedroom_1"
BEDROOM_1_LIGHT = "group.bedroom_1_bulbs"
BEDROOM_1_ECHO = "media_player.bedroom_1_echo"
BEDROOM_1_MOTION = "sensor.bedroom_1_last_5m_motion"

CORRIDOR = "corridor"
CORRIDOR_ECHO = "media_player.corridor_echo"

DINING_AREA_LIGHT = "group.dining_area_bulbs"

GARAGE = "garage"
GARAGE_LIGHT = "group.garage_bulbs"
GARAGE_ECHO = "media_player.garage_echo"
GARAGE_MOTION = "sensor.garage_last_5m_motion"

HALLWAY_MOTION = "group.hallway_motion_sensors"

KITCHEN_LIGHT = "group.kitchen_bulbs"
KITCHEN_MOTION = "group.kitchen_motion_sensors"
KITCHEN_TV = "media_player.kitchen_tv"

LIVING_ROOM = "living_room"
LIVING_ROOM_LIGHT = "group.living_room_bulbs"
LIVING_ROOM_ECHO = "media_player.living_room_echo"
LIVING_ROOM_MOTION = "sensor.living_room_last_5m_motion"
LIVING_ROOM_TV = "sensor.living_room_tv_plug_power_on"

OFFICE_1 = "office_1"
OFFICE_1_LIGHT = "group.office_1_bulbs"
OFFICE_1_ECHO = "media_player.office_1_echo"
OFFICE_1_MOTION = "sensor.office_1_last_5m_motion"
OFFICE_1_TV = "remote.office_1_tv_remote"

OFFICE_2 = "office_2"
OFFICE_2_LIGHT = "group.office_2_bulbs"
OFFICE_2_ECHO = "media_player.office_2_echo"
OFFICE_2_MOTION = "sensor.office_2_last_5m_motion"

QUITE_TIME = "binary_sensor.is_quite_time"

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
  silenced_targets = {f"media_player.{area}_echo" for area in silent_in or ()}

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

  # Mute silenced targets.
  targets = list(targets.difference(silenced_targets))
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
play(hass, data.get("message"), data.get("silent_in"), env=ENV)
