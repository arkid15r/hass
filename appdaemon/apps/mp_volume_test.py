"""Tests for tts_volume.py"""

__author__ = "Ark (ark@cho.red)"

import unittest
from unittest import mock

import mp_volume


class TestAmazonEcho(unittest.TestCase):
  """Amazon Echo volume tests."""

  def setUp(self):
    self.alexa_volume = mp_volume.AmazonEcho(mock.Mock(), mock.Mock(),
                                             mock.MagicMock(), mock.MagicMock(),
                                             mock.Mock(), mock.Mock(),
                                             mock.Mock())
    self.alexa_volume.initialize()

    mp_volume.AmazonEcho.call_service = mock.Mock()

  def _assert_hass_called_with(self, volume_level, areas):
    entity_id = ','.join(
        mp_volume.AmazonEcho.get_target(area) for area in areas)
    volume_level = float(volume_level / 100)

    self.alexa_volume.call_service.assert_called_with("media_player/volume_set",
                                                      entity_id=entity_id,
                                                      volume_level=volume_level)

  def test_set_volume_current_areas(self):
    """Test set volume for current areas."""

    volume_level = 42
    entity_id = self.alexa_volume.set_volume(volume_level,
                                             mp_volume.AmazonEcho.AREAS)
    area_count = len(entity_id.split(','))

    self.assertEqual(area_count, len(mp_volume.AmazonEcho.AREAS))

  def test_set_volume_service_calls(self):
    """Test set volume generates HASS calls."""

    areas = (
        "area1",
        "area2",
    )
    volume_level = 42

    self.alexa_volume.set_volume(volume_level, areas)
    self._assert_hass_called_with(volume_level, areas)

  def test_volume_level_raises_value_error(self):
    """Test invalid volume level raise error."""

    for volume_level in (-1, 110, '110'):
      with self.assertRaises(ValueError) as ctx:
        self.alexa_volume.set_volume(volume_level, ())

      self.assertIn("The volume level must be a number from 0 to 100.",
                    str(ctx.exception))


if __name__ == "__main__":
  unittest.main()
