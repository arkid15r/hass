"""
Play a TTS message on Amazon Echo devices via Alexa notification service.
Generates list of target devices based on time of day and recent motion activity.
"""

__author__ = "Ark (ark@cho.red)"


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

PRIMARY_BATHROOM = "primary_bathroom"
PRIMARY_BATHROOM_LIGHT = "group.primary_bathroom_bulbs"
PRIMARY_BATHROOM_ECHO = "media_player.primary_bathroom_echo"
PRIMARY_BATHROOM_MOTION = "sensor.primary_bathroom_last_5m_motion"

PRIMARY_BEDROOM = "primary_bedroom"
PRIMARY_BEDROOM_LIGHT = "group.primary_bedroom_bulbs"
PRIMARY_BEDROOM_ECHO = "media_player.primary_bedroom_echo"
PRIMARY_BEDROOM_MOTION = "sensor.primary_bedroom_last_5m_motion"

QUITE_TIME = "binary_sensor.is_quite_time"

SECONDARY_BATHROOM = "secondary_bathroom"
SECONDARY_BATHROOM_LIGHT = "group.secondary_bathroom_bulbs"
SECONDARY_BATHROOM_ECHO = "media_player.secondary_bathroom_echo"
SECONDARY_BATHROOM_MOTION = "sensor.secondary_bathroom_last_5m_motion"

STATE_ON = "on"


def make_announcement(hass, message=None, silent_in=None):
    """
    Check targets and generates message request.

    Parameters:
      message (str): A text to announce.
      silent_in (list): A list of devices to exclude from targets.

    Returns:
      list: A list of target devices the message to be announced on.
    """

    def is_not_silenced_in(target):
        """
        Returns True if target is not in silenced list otherwise returns False.
        """

        return target not in silent_in

    def is_on(sensor):
        """
        Returns True if sensor's state is "on" otherwise returns False.
        """

        return hass.states.get(sensor).state == STATE_ON

    if not message:
        raise ValueError("Message is required.")

    if silent_in is None:
        silent_in = ()

    quite_hours = is_on(QUITE_TIME)

    play_in_garage = is_not_silenced_in(GARAGE) and (
        is_on(GARAGE_LIGHT) or is_on(GARAGE_MOTION)
    )

    play_in_living_room = is_not_silenced_in(LIVING_ROOM) and (
        is_on(DINING_AREA_LIGHT)
        or is_on(HALLWAY_MOTION)
        or is_on(KITCHEN_LIGHT)
        or is_on(KITCHEN_MOTION)
        or is_on(LIVING_ROOM_LIGHT)
        or is_on(LIVING_ROOM_MOTION)
        or is_on(LIVING_ROOM_TV)
    )

    play_in_office_1 = is_not_silenced_in(OFFICE_1) and (
        is_on(OFFICE_1_LIGHT) or is_on(OFFICE_1_MOTION) or is_on(OFFICE_1_TV)
    )

    play_in_office_2 = is_not_silenced_in(OFFICE_2) and (
        is_on(OFFICE_2_LIGHT) or is_on(OFFICE_2_MOTION)
    )

    play_in_primary_bathroom = is_not_silenced_in(PRIMARY_BATHROOM) and (
        is_on(PRIMARY_BATHROOM_LIGHT) or is_on(PRIMARY_BATHROOM_MOTION)
    )

    play_in_primary_bedroom = is_not_silenced_in(PRIMARY_BEDROOM) and (
        is_on(PRIMARY_BEDROOM_LIGHT)
        or is_on(PRIMARY_BEDROOM_MOTION)
        or quite_hours  # The default target for quite hours.
    )

    play_in_secondary_bathroom = is_not_silenced_in(SECONDARY_BATHROOM) and (
        is_on(SECONDARY_BATHROOM_LIGHT) or is_on(SECONDARY_BATHROOM_MOTION)
    )

    targets = set()

    if play_in_garage:
        targets.add(GARAGE_ECHO)

    if play_in_living_room:
        targets.add(LIVING_ROOM_ECHO)

    if play_in_office_1:
        targets.add(OFFICE_1_ECHO)

    if play_in_office_2:
        targets.add(OFFICE_2_ECHO)

    if play_in_primary_bathroom:
        targets.add(PRIMARY_BATHROOM_ECHO)

    if play_in_primary_bedroom:
        targets.add(PRIMARY_BEDROOM_ECHO)

    if play_in_secondary_bathroom:
        targets.add(SECONDARY_BATHROOM_ECHO)

    # The default target for regular hours.
    if not targets and not quite_hours:
        targets.add(CORRIDOR_ECHO)

    targets = list(targets)
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


make_announcement(hass, data.get("message"), data.get("silent_in"))  # pylint: disable=undefined-variable
