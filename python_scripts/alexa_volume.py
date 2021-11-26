"""Sets the volume level on Amazon Echo devices."""

__author__ = "Ark (ark@cho.red)"

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


def set_volume(hass, targets, volume_level):
  """Set volume level for a set of devices.

    Parameters:
      hass: A HomeAssistant service from the global context.
      targets: A list of device identifiers.
      volume_level: A volume level to set.

    """

  error_message = "The volume level must be a number within the range [0..1]."

  try:
    volume_level = float(volume_level)
  except ValueError as e:
    raise ValueError(error_message) from e

  if volume_level < 0 or volume_level > 1:
    raise ValueError(error_message)

  hass.services.call(
      "media_player",
      "volume_set",
      {
          "entity_id":
              ', '.join(f"media_player.{target}" for target in targets),
          "volume_level":
              volume_level
      },
  )


# pylint: disable=undefined-variable
set_volume(hass, DEVICES, data.get("volume_level"))
