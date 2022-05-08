"""Sets the volume level on media player devices."""

__author__ = 'Ark (ark@cho.red)'

from appdaemon.plugins.hass import hassapi as hass


class AmazonEcho(hass.Hass):
  """Amazon Echo App Daemon class."""

  AREAS = (
      'bathroom_1',
      'bathroom_2',
      'bedroom_1',
      'garage',
      'great_room',
      'office_1',
      'office_2',
      'stairway',
  )
  EVENT_NAME = 'mp_volume'

  def initialize(self):
    """Initialize event listener."""

    self.listen_event(self.handle_event, self.EVENT_NAME)

  @staticmethod
  def get_target(area):
    """Return media player target ID for an area."""

    return f'media_player.{area}_echo'

  # pylint: disable=unused-argument
  def handle_event(self, event, data, kwargs):
    """Handle the event."""

    self.set_volume(data.get('volume_level'), data.get('areas', self.AREAS))

  def set_volume(self, volume_level, areas):
    """Set volume level for a set of devices.

      Parameters:
        volume_level: A volume level to set.
        areas: A list of areas.
      Returns:
        string: a comma separated list of the targets for HASS API call.
      """

    error_message = 'The volume level must be a number from 0 to 100.'

    try:
      volume_level = float(volume_level)
    except ValueError as e:
      raise ValueError(error_message) from e

    if volume_level < 0 or volume_level > 100:
      raise ValueError(error_message)

    entity_id = ','.join(AmazonEcho.get_target(area) for area in areas)
    volume_level = float(volume_level / 100)

    self.call_service('media_player/volume_set',
                      entity_id=entity_id,
                      volume_level=volume_level)

    return entity_id
