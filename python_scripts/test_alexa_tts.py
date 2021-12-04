"""Tests for alexa_tts.py"""

__author__ = "Ark (ark@cho.red)"

# pylint: disable=missing-function-docstring

import unittest
from unittest import mock

import alexa_tts


class StatesMock:
  """A mock for hass states container."""

  def __init__(self):
    self.values = {}

  def __delitem__(self, name):
    del self.values[name]

  def __setitem__(self, name, value):
    self.values[name] = value

  def __iter__(self):
    return iter(self.values)

  def __getitem__(self, name):
    if name in self.values:
      return self.values[name]

    return TestBase.sensor_off

  get = __getitem__


class TestBase(unittest.TestCase):
  """A base class for tests."""

  sensor_off = mock.Mock()
  sensor_on = mock.Mock()

  def setUp(self):
    type(self.sensor_off).state = mock.PropertyMock(return_value="off")
    type(self.sensor_on).state = mock.PropertyMock(return_value="on")

    self.hass = mock.Mock()
    self.hass.states = StatesMock()
    self.hass.services = mock.Mock()

    self.default_targets = [alexa_tts.CORRIDOR_ECHO]
    self.test_message = "Test message."

  def _assert_hass_called_with(self, message, targets):
    self.hass.services.call.assert_called_with(
        "notify",
        "alexa_media",
        {
            "data": {
                "type": "tts"
            },
            "message": message,
            "target": targets,
        },
    )

  def _assert_hass_called_with_defaults(self):
    return self._assert_hass_called_with(self.test_message,
                                         self.default_targets)

  def _assert_hass_not_called(self):
    self.hass.services.call.assert_not_called()


class TestArgs(unittest.TestCase):
  """Test input args."""

  def test_no_message_raises_value_error(self):
    """Test no message handler."""

    with self.assertRaises(ValueError) as ctx:
      alexa_tts.play({})

      self.assertIn("Message is required", str(ctx.exception))

    with self.assertRaises(ValueError) as ctx:
      alexa_tts.play({}, message="")

      self.assertIn("Message is required", str(ctx.exception))


class TestDefaultTargets(TestBase):
  """Default targets tests."""

  def _test_not_played(self, targets, env=None):
    """Assert message was not played on the default targets."""

    expected_targets = alexa_tts.play(self.hass,
                                      message=self.test_message,
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
    """Assert message was played on the default target."""

    silent_in = None
    if silent_targets:
      silent_in = silent_targets.keys()

    expected_targets = alexa_tts.play(self.hass,
                                      message=self.test_message,
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

    self._assert_hass_called_with(self.test_message, expected_targets)


class TestDefaultTargetsNormalTime(TestDefaultTargets):
  """Default targets normal time tests."""

  def test_not_played(self):
    default_targets = {
        alexa_tts.OFFICE_1: alexa_tts.OFFICE_1_ECHO,
        alexa_tts.OFFICE_2: alexa_tts.OFFICE_2_ECHO,
    }
    super()._test_not_played(
        default_targets, env={"NORMAL_TIME_DEFAULT_TARGETS": default_targets})

    # Test current targets.
    super()._test_not_played(alexa_tts.ENV["NORMAL_TIME_DEFAULT_TARGETS"],
                             env=alexa_tts.ENV)

  def test_played(self):
    default_targets = {
        alexa_tts.OFFICE_1: alexa_tts.OFFICE_1_ECHO,
        alexa_tts.OFFICE_2: alexa_tts.OFFICE_2_ECHO,
    }
    super()._test_played(default_targets,
                         env={"NORMAL_TIME_DEFAULT_TARGETS": default_targets})

    # Test current targets.
    super()._test_played(alexa_tts.ENV["NORMAL_TIME_DEFAULT_TARGETS"],
                         env=alexa_tts.ENV)


class TestDefaultTargetsQuiteTime(TestDefaultTargets):
  """Default targets quite time tests."""

  def test_not_played(self):
    default_targets = {
        alexa_tts.OFFICE_1: alexa_tts.OFFICE_1_ECHO,
        alexa_tts.OFFICE_2: alexa_tts.OFFICE_2_ECHO,
    }
    with mock.patch.dict(self.hass.states,
                         {alexa_tts.QUITE_TIME: self.sensor_on}):
      super()._test_not_played(default_targets,
                               {"QUITE_TIME_DEFAULT_TARGETS": default_targets})

      # Test current targets.
      super()._test_not_played(alexa_tts.ENV["QUITE_TIME_DEFAULT_TARGETS"],
                               env=alexa_tts.ENV)

  def test_played(self):
    default_targets = {
        alexa_tts.OFFICE_1: alexa_tts.OFFICE_1_ECHO,
        alexa_tts.OFFICE_2: alexa_tts.OFFICE_2_ECHO,
    }
    with mock.patch.dict(self.hass.states,
                         {alexa_tts.QUITE_TIME: self.sensor_on}):
      super()._test_played(default_targets,
                           env={"QUITE_TIME_DEFAULT_TARGETS": default_targets})

      # Test current targets.
      super()._test_played(alexa_tts.ENV["QUITE_TIME_DEFAULT_TARGETS"],
                           env=alexa_tts.ENV)


class TestLastResortTargetsNormalTime(TestDefaultTargets):
  """Last resort targets normal time tests."""

  def test_not_played(self):
    default_targets = {
        alexa_tts.OFFICE_1: alexa_tts.OFFICE_1_ECHO,
        alexa_tts.OFFICE_2: alexa_tts.OFFICE_2_ECHO,
    }
    super()._test_not_played(
        default_targets, {"NORMAL_TIME_LAST_RESORT_TARGETS": default_targets})

    # Test current targets.
    super()._test_not_played(alexa_tts.ENV["NORMAL_TIME_LAST_RESORT_TARGETS"],
                             env=alexa_tts.ENV)

  def test_played(self):
    default_targets = {
        alexa_tts.OFFICE_1: alexa_tts.OFFICE_1_ECHO,
        alexa_tts.OFFICE_2: alexa_tts.OFFICE_2_ECHO,
    }
    super()._test_played(
        default_targets,
        env={"NORMAL_TIME_LAST_RESORT_TARGETS": default_targets})

    # Test current targets.
    super()._test_played(alexa_tts.ENV["NORMAL_TIME_LAST_RESORT_TARGETS"],
                         env=alexa_tts.ENV)

    with mock.patch.dict(self.hass.states,
                         {alexa_tts.LIVING_ROOM_MOTION: self.sensor_on}):
      super()._test_played(alexa_tts.ENV["NORMAL_TIME_LAST_RESORT_TARGETS"],
                           silent_targets={
                               alexa_tts.LIVING_ROOM:
                                   alexa_tts.LIVING_ROOM_ECHO,
                           },
                           env=alexa_tts.ENV)


class TestTarget(TestBase):
  """A base class for specific target behavior tests."""

  def _test_not_played_normal_time(self, area, target, conditions):
    """Assert message was not played on the target during normal time. """

    for condition in conditions:
      targets = alexa_tts.play(
          self.hass,
          message=self.test_message,
          silent_in=[target],
          env=alexa_tts.ENV,
      )
      with mock.patch.dict(self.hass.states, {condition: self.sensor_on}):
        self.assertNotIn(
            target,
            targets,
            f"Should not play in the {area} {conditions[condition]}.",
        )
        self._assert_hass_called_with(self.test_message, targets)

  def _test_played_normal_time(self, area, target, conditions):
    """Assert message was played on the target during normal time."""

    expected_targets = [target]

    for condition in conditions:
      with mock.patch.dict(self.hass.states, {condition: self.sensor_on}):
        targets = alexa_tts.play(self.hass,
                                 message=self.test_message,
                                 env=alexa_tts.ENV)

        self.assertEqual(
            targets,
            expected_targets,
            f"Should play in the {area} {conditions[condition]}.",
        )
        self._assert_hass_called_with(self.test_message, expected_targets)

  def _test_not_played_quite_time(self, area, target, conditions):
    """Assert message was not played on the target during quite time."""

    with mock.patch.dict(self.hass.states,
                         {alexa_tts.QUITE_TIME: self.sensor_on}):
      for condition in conditions:
        with mock.patch.dict(self.hass.states, {condition: self.sensor_on}):
          expected_targets = alexa_tts.play(
              self.hass,
              message=self.test_message,
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
    Assert message was not played on the target due to unless rule conditions.
    """

    condition_dict = {}
    for condition in tuple(conditions.keys()) + unless["conditions"]:
      condition_dict[condition] = self.sensor_on

    with mock.patch.dict(self.hass.states, condition_dict):
      targets = alexa_tts.play(
          self.hass,
          message=self.test_message,
          env=alexa_tts.ENV,
      )

      self.assertNotIn(
          target,
          targets,
          f"Should not play in the {area} when {unless['description']}.",
      )
      self._assert_hass_called_with(self.test_message, targets)

  def _test_played_quite_time(self, area, target):
    """Assert message was  played on the target during quite time. """
    with mock.patch.dict(self.hass.states,
                         {alexa_tts.QUITE_TIME: self.sensor_on}):
      expected_targets = alexa_tts.play(
          self.hass,
          message=self.test_message,
          env={"QUITE_TIME_DEFAULT_TARGETS": {
              area: target
          }},
      )

      self.assertIn(
          target,
          expected_targets,
          f"Should play in the {area} during quite time.",
      )
      self._assert_hass_called_with(self.test_message, expected_targets)


class TestBathroom1(TestTarget):
  """Bathroom 1 tests."""

  conditions = {
      alexa_tts.BATHROOM_1_LIGHT: "the light is on",
      alexa_tts.BATHROOM_1_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(alexa_tts.BATHROOM_1,
                                         alexa_tts.BATHROOM_2_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(alexa_tts.BATHROOM_1,
                                        alexa_tts.BATHROOM_1_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(alexa_tts.BATHROOM_1,
                                     alexa_tts.BATHROOM_1_ECHO, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(alexa_tts.BATHROOM_1,
                                    alexa_tts.BATHROOM_1_ECHO)

  def test_played_unless(self):
    unless = {
        "conditions": (alexa_tts.BATHROOM_1_DOOR, alexa_tts.BEDROOM_1_LIGHT),
        "description":
            f"playing in {alexa_tts.BEDROOM_1} and {alexa_tts.BATHROOM_1} door is open"
    }

    super()._test_played_unless(alexa_tts.BATHROOM_1, alexa_tts.BATHROOM_1_ECHO,
                                self.conditions, unless)


class TestBathroom2(TestTarget):
  """Bathroom 2 tests."""

  conditions = {
      alexa_tts.BATHROOM_2_LIGHT: "the light is on",
      alexa_tts.BATHROOM_2_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(alexa_tts.BATHROOM_2,
                                         alexa_tts.BATHROOM_2_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(alexa_tts.BATHROOM_2,
                                        alexa_tts.BATHROOM_2_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(
        alexa_tts.BATHROOM_2,
        alexa_tts.BATHROOM_2_ECHO,
        self.conditions,
    )

  def test_played_quite_time(self):
    super()._test_played_quite_time(alexa_tts.BATHROOM_2,
                                    alexa_tts.BATHROOM_2_ECHO)

  def test_played_unless(self):
    unless = {
        "conditions": (alexa_tts.BATHROOM_2_DOOR, alexa_tts.LIVING_ROOM_LIGHT),
        "description":
            f"playing in {alexa_tts.LIVING_ROOM} and {alexa_tts.BATHROOM_2} door is open"
    }

    super()._test_played_unless(alexa_tts.BATHROOM_2, alexa_tts.BATHROOM_2_ECHO,
                                self.conditions, unless)


class TestBedroom1(TestTarget):
  """Bedroom 1 tests."""

  conditions = {
      alexa_tts.BEDROOM_1_LIGHT: "the light is on",
      alexa_tts.BEDROOM_1_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(alexa_tts.BEDROOM_1,
                                         alexa_tts.BEDROOM_1_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(alexa_tts.BEDROOM_1,
                                        alexa_tts.BEDROOM_1_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(alexa_tts.BEDROOM_1,
                                     alexa_tts.BEDROOM_1_ECHO, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(alexa_tts.BEDROOM_1,
                                    alexa_tts.BEDROOM_1_ECHO)


class TestGarage(TestTarget):
  """Garage tests."""

  conditions = {
      alexa_tts.GARAGE_LIGHT: "the light is on",
      alexa_tts.GARAGE_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(alexa_tts.GARAGE,
                                         alexa_tts.GARAGE_ECHO, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(alexa_tts.GARAGE, alexa_tts.GARAGE_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(alexa_tts.GARAGE, alexa_tts.GARAGE_ECHO,
                                     self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(alexa_tts.GARAGE, alexa_tts.GARAGE_ECHO)


class TestLivingRoom(TestTarget):
  """Living room tests."""

  conditions = {
      alexa_tts.DINING_AREA_LIGHT:
          "the dining area light is on",
      alexa_tts.HALLWAY_MOTION:
          "there was a recent motion in the hallway",
      alexa_tts.KITCHEN_LIGHT:
          "the kitchen light is on",
      alexa_tts.KITCHEN_MOTION:
          "there was a recent motion in the kitchen",
      alexa_tts.LIVING_ROOM_LIGHT:
          "the living room light is on",
      alexa_tts.LIVING_ROOM_MOTION:
          "there was a recent motion in the living room",
      alexa_tts.LIVING_ROOM_TV:
          "the living room TV is on",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(alexa_tts.LIVING_ROOM,
                                         alexa_tts.LIVING_ROOM_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(alexa_tts.LIVING_ROOM,
                                        alexa_tts.LIVING_ROOM_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(alexa_tts.LIVING_ROOM,
                                     alexa_tts.LIVING_ROOM_ECHO,
                                     self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(alexa_tts.LIVING_ROOM,
                                    alexa_tts.LIVING_ROOM_ECHO)


class TestOffice1(TestTarget):
  """Office1 tests."""

  conditions = {
      alexa_tts.OFFICE_1_LIGHT: "the light is on",
      alexa_tts.OFFICE_1_MOTION: "there was a recent motion",
      alexa_tts.OFFICE_1_TV: "the TV is on",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(alexa_tts.OFFICE_1,
                                         alexa_tts.OFFICE_1_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(alexa_tts.OFFICE_1,
                                        alexa_tts.OFFICE_1_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(alexa_tts.OFFICE_1,
                                     alexa_tts.OFFICE_1_ECHO, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(alexa_tts.OFFICE_1, alexa_tts.OFFICE_1_ECHO)

  def test_played_unless(self):
    unless = {
        "conditions": (alexa_tts.DINING_AREA_LIGHT, alexa_tts.KITCHEN_LIGHT,
                       alexa_tts.LIVING_ROOM_LIGHT, alexa_tts.LIVING_ROOM_TV),
        "description": f"playing in {alexa_tts.LIVING_ROOM}"
    }

    super()._test_played_unless(alexa_tts.OFFICE_1, alexa_tts.OFFICE_1_ECHO,
                                self.conditions, unless)


class TestOffice2(TestTarget):
  """Office2 tests."""

  conditions = {
      alexa_tts.OFFICE_2_LIGHT: "the light is on",
      alexa_tts.OFFICE_2_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(alexa_tts.OFFICE_2,
                                         alexa_tts.OFFICE_2_ECHO,
                                         self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(alexa_tts.OFFICE_2,
                                        alexa_tts.OFFICE_2_ECHO,
                                        self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(alexa_tts.OFFICE_2,
                                     alexa_tts.OFFICE_2_ECHO, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(alexa_tts.OFFICE_2, alexa_tts.OFFICE_2_ECHO)


if __name__ == "__main__":
  unittest.main()
