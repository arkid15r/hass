"""Tests for tts.py"""

__author__ = "Ark (ark@cho.red)"

# pylint: disable=cell-var-from-loop
# pylint: disable=missing-function-docstring

import unittest
from unittest import mock

import tts


class TestBase(unittest.TestCase):
  """A base class for tests."""

  states = {}

  def setUp(self):
    self.default_targets = [tts.Alexa.CORRIDOR_ECHO]
    self.text = "Test text."

    self.alexa = tts.Alexa(mock.Mock(), mock.Mock(), mock.MagicMock(),
                           mock.MagicMock(), mock.Mock(), mock.Mock(),
                           mock.Mock())

    tts.Alexa.call_service = mock.Mock()
    tts.Alexa.get_state = mock.Mock()

  def _assert_hass_called_with(self, text, targets):
    self.alexa.call_service.assert_called_with("notify/alexa_media",
                                               target=targets,
                                               message=text,
                                               data={"type": "tts"})

  def _assert_hass_called_with_defaults(self):
    return self._assert_hass_called_with(self.text, self.default_targets)

  def _assert_hass_not_called(self):
    self.alexa.call_service.assert_not_called()


class TestArgs(TestBase):
  """Test input args."""

  def test_no_text_raises_value_error(self):
    """Test no text handler."""

    with self.assertRaises(ValueError) as ctx:
      self.alexa.tts()

      self.assertIn("text is required", str(ctx.exception))

    with self.assertRaises(ValueError) as ctx:
      self.alexa.tts(text="")

      self.assertIn("text is required", str(ctx.exception))


class TestDefaultTargets(TestBase):
  """Default targets tests."""

  def _test_not_played(self, targets, env=None):
    """Assert text was not played on the default targets."""

    expected_targets = self.alexa.tts(text=self.text,
                                      silent_in=targets.keys(),
                                      env=env)
    for area in targets:
      self.assertNotIn(
          targets[area],
          expected_targets,
          f"Should not play on the default target in {area} if silenced.",
      )
      self._assert_hass_not_called()

  def _test_played(self, targets, silent_targets=None, env=None):
    """Assert text was played on the default target."""

    silent_in = None
    if silent_targets:
      silent_in = silent_targets.keys()

    expected_targets = self.alexa.tts(text=self.text,
                                      silent_in=silent_in,
                                      env=env)

    for area in targets:
      self.assertIn(
          targets[area],
          expected_targets,
          f"Should play on the default target in {area}.",
      )

    for area in silent_targets or ():
      self.assertNotIn(
          silent_targets[area],
          expected_targets,
          f"Should not play on the target in {area} if silenced.",
      )

    self._assert_hass_called_with(self.text, expected_targets)


class TestDefaultTargetsNormalTime(TestDefaultTargets):
  """Default targets normal time tests."""

  def test_not_played(self):
    default_targets = {
        tts.Alexa.OFFICE_1: tts.Alexa.OFFICE_1_ECHO,
        tts.Alexa.OFFICE_2: tts.Alexa.OFFICE_2_ECHO,
    }
    super()._test_not_played(
        default_targets, env={"NORMAL_TIME_DEFAULT_TARGETS": default_targets})

    # Test current targets.
    super()._test_not_played(tts.Alexa.ENV["NORMAL_TIME_DEFAULT_TARGETS"],
                             env=tts.Alexa.ENV)

  def test_played(self):
    default_targets = {
        tts.Alexa.OFFICE_1: tts.Alexa.OFFICE_1_ECHO,
        tts.Alexa.OFFICE_2: tts.Alexa.OFFICE_2_ECHO,
    }
    super()._test_played(default_targets,
                         env={"NORMAL_TIME_DEFAULT_TARGETS": default_targets})

    # Test current targets.
    super()._test_played(tts.Alexa.ENV["NORMAL_TIME_DEFAULT_TARGETS"],
                         env=tts.Alexa.ENV)


class TestDefaultTargetsQuiteTime(TestDefaultTargets):
  """Default targets quite time tests."""

  def test_not_played(self):
    default_targets = {
        tts.Alexa.OFFICE_1: tts.Alexa.OFFICE_1_ECHO,
        tts.Alexa.OFFICE_2: tts.Alexa.OFFICE_2_ECHO,
    }
    self.alexa.get_state.side_effect = lambda sensor: {
        tts.Alexa.QUITE_TIME: tts.Alexa.STATE_ON
    }.get(sensor, tts.Alexa.STATE_OFF)
    super()._test_not_played(default_targets,
                             {"QUITE_TIME_DEFAULT_TARGETS": default_targets})

    # Test current targets.
    super()._test_not_played(tts.Alexa.ENV["QUITE_TIME_DEFAULT_TARGETS"],
                             env=tts.Alexa.ENV)

  def test_played(self):
    default_targets = {
        tts.Alexa.OFFICE_1: tts.Alexa.OFFICE_1_ECHO,
        tts.Alexa.OFFICE_2: tts.Alexa.OFFICE_2_ECHO,
    }
    self.alexa.get_state.side_effect = lambda sensor: {
        tts.Alexa.QUITE_TIME: tts.Alexa.STATE_ON
    }.get(sensor, tts.Alexa.STATE_OFF)
    super()._test_played(default_targets,
                         env={"QUITE_TIME_DEFAULT_TARGETS": default_targets})

    # Test current targets.
    super()._test_played(tts.Alexa.ENV["QUITE_TIME_DEFAULT_TARGETS"],
                         env=tts.Alexa.ENV)


class TestLastResortTargetsNormalTime(TestDefaultTargets):
  """Last resort targets normal time tests."""

  def test_not_played(self):
    default_targets = {
        tts.Alexa.OFFICE_1: tts.Alexa.OFFICE_1_ECHO,
        tts.Alexa.OFFICE_2: tts.Alexa.OFFICE_2_ECHO,
    }
    super()._test_not_played(
        default_targets, {"NORMAL_TIME_LAST_RESORT_TARGETS": default_targets})

    # Test current targets.
    super()._test_not_played(tts.Alexa.ENV["NORMAL_TIME_LAST_RESORT_TARGETS"],
                             env=tts.Alexa.ENV)

  def test_played(self):
    default_targets = {
        tts.Alexa.OFFICE_1: tts.Alexa.OFFICE_1_ECHO,
        tts.Alexa.OFFICE_2: tts.Alexa.OFFICE_2_ECHO,
    }
    super()._test_played(
        default_targets,
        env={"NORMAL_TIME_LAST_RESORT_TARGETS": default_targets})

    # Test current targets.
    super()._test_played(tts.Alexa.ENV["NORMAL_TIME_LAST_RESORT_TARGETS"],
                         env=tts.Alexa.ENV)

    self.alexa.get_state.side_effect = lambda sensor: {
        tts.Alexa.LIVING_ROOM_MOTION: tts.Alexa.STATE_ON
    }.get(sensor, tts.Alexa.STATE_OFF)
    super()._test_played(tts.Alexa.ENV["NORMAL_TIME_LAST_RESORT_TARGETS"],
                         silent_targets={
                             tts.Alexa.LIVING_ROOM: tts.Alexa.LIVING_ROOM_ECHO,
                         },
                         env=tts.Alexa.ENV)


class TestTarget(TestBase):
  """A base class for specific target behavior tests."""

  def _test_not_played_normal_time(self, area, target, conditions):
    """Assert text was not played on the target during normal time. """

    for condition in conditions:
      self.alexa.get_state.side_effect = lambda sensor: {
          condition: tts.Alexa.STATE_ON
      }.get(sensor, tts.Alexa.STATE_OFF)

      targets = self.alexa.tts(
          text=self.text,
          silent_in=[area],
          env=tts.Alexa.ENV,
      )
      self.assertNotIn(
          target,
          targets,
          f"Should not play in the {area} if silenced and "
          f"{conditions[condition]}.",
      )
      self._assert_hass_called_with(self.text, targets)

  def _test_played_normal_time(self, area, target, conditions):
    """Assert text was played on the target during normal time."""

    expected_targets = [target]

    for condition in conditions:
      self.alexa.get_state.side_effect = lambda sensor: {
          condition: tts.Alexa.STATE_ON
      }.get(sensor, tts.Alexa.STATE_OFF)
      targets = self.alexa.tts(text=self.text, env=tts.Alexa.ENV)

      self.assertEqual(
          targets,
          expected_targets,
          f"Should play in the {area} if {conditions[condition]}.",
      )
      self._assert_hass_called_with(self.text, expected_targets)

  def _test_not_played_quite_time(self, area, target, conditions):
    """Assert text was not played on the target during quite time."""

    for condition in conditions:
      self.alexa.get_state.side_effect = lambda sensor: {
          condition: tts.Alexa.STATE_ON,
          tts.Alexa.QUITE_TIME: tts.Alexa.STATE_ON
      }.get(sensor, tts.Alexa.STATE_OFF)

      expected_targets = self.alexa.tts(
          text=self.text,
          silent_in=[area],
          env={"QUITE_TIME_DEFAULT_TARGETS": {
              area: target
          }},
      )

      self.assertNotIn(
          target,
          expected_targets,
          f"Should not play in the {area} during quite time if silenced.",
      )
      self._assert_hass_not_called()

  def _test_played_unless(self, area, target, conditions, unless):
    """
    Assert text was not played on the target due to unless rule conditions.
    """

    condition_dict = {}
    for condition in tuple(conditions.keys()) + unless["conditions"]:
      condition_dict[condition] = tts.Alexa.STATE_ON

    self.alexa.get_state.side_effect = lambda sensor: condition_dict.get(
        sensor, tts.Alexa.STATE_OFF)

    targets = self.alexa.tts(
        text=self.text,
        env=tts.Alexa.ENV,
    )

    self.assertNotIn(
        target,
        targets,
        f"Should not play in the {area} when {unless['description']}.",
    )
    self._assert_hass_called_with(self.text, targets)

  def _test_played_quite_time(self, area, target):
    """Assert text was  played on the target during quite time. """

    self.alexa.get_state.side_effect = lambda sensor: {
        tts.Alexa.QUITE_TIME: tts.Alexa.STATE_ON
    }.get(sensor, tts.Alexa.STATE_OFF)

    expected_targets = self.alexa.tts(
        text=self.text,
        env={"QUITE_TIME_DEFAULT_TARGETS": {
            area: target
        }},
    )

    self.assertIn(
        target,
        expected_targets,
        f"Should play in the {area} during quite time.",
    )
    self._assert_hass_called_with(self.text, expected_targets)


class TestBathroom1(TestTarget):
  """Bathroom 1 tests."""

  conditions = {
      tts.Alexa.BATHROOM_1_LIGHT: "the light is on",
      tts.Alexa.BATHROOM_1_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(tts.Alexa.BATHROOM_1,
                                         tts.Alexa.BATHROOM_2_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(tts.Alexa.BATHROOM_1,
                                        tts.Alexa.BATHROOM_1_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(tts.Alexa.BATHROOM_1,
                                     tts.Alexa.BATHROOM_1_ECHO, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(tts.Alexa.BATHROOM_1,
                                    tts.Alexa.BATHROOM_1_ECHO)

  def test_played_unless(self):
    unless = {
        "conditions": (tts.Alexa.BATHROOM_1_DOOR, tts.Alexa.BEDROOM_1_LIGHT),
        "description":
            f"playing in {tts.Alexa.BEDROOM_1} and {tts.Alexa.BATHROOM_1} door is open"
    }

    super()._test_played_unless(tts.Alexa.BATHROOM_1, tts.Alexa.BATHROOM_1_ECHO,
                                self.conditions, unless)


class TestBathroom2(TestTarget):
  """Bathroom 2 tests."""

  conditions = {
      tts.Alexa.BATHROOM_2_LIGHT: "the light is on",
      tts.Alexa.BATHROOM_2_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(tts.Alexa.BATHROOM_2,
                                         tts.Alexa.BATHROOM_2_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(tts.Alexa.BATHROOM_2,
                                        tts.Alexa.BATHROOM_2_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(
        tts.Alexa.BATHROOM_2,
        tts.Alexa.BATHROOM_2_ECHO,
        self.conditions,
    )

  def test_played_quite_time(self):
    super()._test_played_quite_time(tts.Alexa.BATHROOM_2,
                                    tts.Alexa.BATHROOM_2_ECHO)

  def test_played_unless(self):
    unless = {
        "conditions": (tts.Alexa.BATHROOM_2_DOOR, tts.Alexa.LIVING_ROOM_LIGHT),
        "description":
            f"playing in {tts.Alexa.LIVING_ROOM} and {tts.Alexa.BATHROOM_2} door is open"
    }

    super()._test_played_unless(tts.Alexa.BATHROOM_2, tts.Alexa.BATHROOM_2_ECHO,
                                self.conditions, unless)


class TestBedroom1(TestTarget):
  """Bedroom 1 tests."""

  conditions = {
      tts.Alexa.BEDROOM_1_LIGHT: "the light is on",
      tts.Alexa.BEDROOM_1_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(tts.Alexa.BEDROOM_1,
                                         tts.Alexa.BEDROOM_1_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(tts.Alexa.BEDROOM_1,
                                        tts.Alexa.BEDROOM_1_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(tts.Alexa.BEDROOM_1,
                                     tts.Alexa.BEDROOM_1_ECHO, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(tts.Alexa.BEDROOM_1,
                                    tts.Alexa.BEDROOM_1_ECHO)


class TestGarage(TestTarget):
  """Garage tests."""

  conditions = {
      tts.Alexa.GARAGE_LIGHT: "the light is on",
      tts.Alexa.GARAGE_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(tts.Alexa.GARAGE,
                                         tts.Alexa.GARAGE_ECHO, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(tts.Alexa.GARAGE, tts.Alexa.GARAGE_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(tts.Alexa.GARAGE, tts.Alexa.GARAGE_ECHO,
                                     self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(tts.Alexa.GARAGE, tts.Alexa.GARAGE_ECHO)


class TestLivingRoom(TestTarget):
  """Living room tests."""

  conditions = {
      tts.Alexa.DINING_AREA_LIGHT:
          "the dining area light is on",
      tts.Alexa.HALLWAY_MOTION:
          "there was a recent motion in the hallway",
      tts.Alexa.KITCHEN_LIGHT:
          "the kitchen light is on",
      tts.Alexa.KITCHEN_MOTION:
          "there was a recent motion in the kitchen",
      tts.Alexa.LIVING_ROOM_LIGHT:
          "the living room light is on",
      tts.Alexa.LIVING_ROOM_MOTION:
          "there was a recent motion in the living room",
      tts.Alexa.LIVING_ROOM_TV:
          "the living room TV is on",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(tts.Alexa.LIVING_ROOM,
                                         tts.Alexa.LIVING_ROOM_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(tts.Alexa.LIVING_ROOM,
                                        tts.Alexa.LIVING_ROOM_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(tts.Alexa.LIVING_ROOM,
                                     tts.Alexa.LIVING_ROOM_ECHO,
                                     self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(tts.Alexa.LIVING_ROOM,
                                    tts.Alexa.LIVING_ROOM_ECHO)


class TestOffice1(TestTarget):
  """Office1 tests."""

  conditions = {
      tts.Alexa.OFFICE_1_LIGHT: "the light is on",
      tts.Alexa.OFFICE_1_MOTION: "there was a recent motion",
      tts.Alexa.OFFICE_1_TV: "the TV is on",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(tts.Alexa.OFFICE_1,
                                         tts.Alexa.OFFICE_1_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(tts.Alexa.OFFICE_1,
                                        tts.Alexa.OFFICE_1_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(tts.Alexa.OFFICE_1,
                                     tts.Alexa.OFFICE_1_ECHO, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(tts.Alexa.OFFICE_1, tts.Alexa.OFFICE_1_ECHO)

  def test_played_unless(self):
    unless = {
        "conditions": (tts.Alexa.DINING_AREA_LIGHT, tts.Alexa.KITCHEN_LIGHT,
                       tts.Alexa.LIVING_ROOM_LIGHT, tts.Alexa.LIVING_ROOM_TV),
        "description": f"playing in {tts.Alexa.LIVING_ROOM}"
    }

    super()._test_played_unless(tts.Alexa.OFFICE_1, tts.Alexa.OFFICE_1_ECHO,
                                self.conditions, unless)


class TestOffice2(TestTarget):
  """Office2 tests."""

  conditions = {
      tts.Alexa.OFFICE_2_LIGHT: "the light is on",
      tts.Alexa.OFFICE_2_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(tts.Alexa.OFFICE_2,
                                         tts.Alexa.OFFICE_2_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(tts.Alexa.OFFICE_2,
                                        tts.Alexa.OFFICE_2_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(tts.Alexa.OFFICE_2,
                                     tts.Alexa.OFFICE_2_ECHO, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(tts.Alexa.OFFICE_2, tts.Alexa.OFFICE_2_ECHO)


if __name__ == "__main__":
  unittest.main()
