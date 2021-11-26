"""Tests for alexa_volume.py"""

__author__ = "Ark (ark@cho.red)"

import unittest
from unittest import mock

import alexa_volume


class TestBase(unittest.TestCase):
  """A base class for tests."""

  def setUp(self):
    self.hass = mock.Mock()
    self.hass.services = mock.Mock()

  def _assert_hass_called_with(
      self,
      targets,
      volume_level,
  ):
    self.hass.services.call.assert_called_with(
        "media_player",
        "volume_set",
        {
            "entity_id":
                ', '.join(f"media_player.{target}" for target in targets),
            "volume_level":
                volume_level,
        },
    )


class TestAlexaVolume(TestBase):
  """Alexa volume tests."""

  def test_set_volume_hass_calls(self):
    """Test set volume generates HASS calls."""

    targets = (
        "test_target1",
        "test_target2",
    )
    volume_level = 0.42

    alexa_volume.set_volume(self.hass, targets, volume_level)
    self._assert_hass_called_with(targets, volume_level)

  def test_volume_level_raises_value_error(self):
    """Test invalid volume level values."""

    for value in (-1, 1.1, '1.1'):
      with self.assertRaises(ValueError) as ctx:
        alexa_volume.set_volume(self.hass, (), value)

      self.assertIn("The volume level must be a number within the range [0..1]",
                    str(ctx.exception))


if __name__ == "__main__":
  unittest.main()
