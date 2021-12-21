"""Tests for tts.py"""

__author__ = "Ark (ark@cho.red)"

# pylint: disable=cell-var-from-loop
# pylint: disable=missing-function-docstring

import unittest
from unittest import mock

import yaml  # pylint: disable=import-error

import tts


class TestBase(unittest.TestCase):
  """A base class for tests."""

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

  env = {}
  rules = {}
  quite_time = {}

  states = {}

  @classmethod
  def setUpClass(cls):
    with open("apps.yaml", 'r', encoding='utf-8') as config_file:
      config = yaml.safe_load(config_file)["tts"]

    cls.env = config["env"]
    cls.rules = config["rules"]
    cls.quite_time = config["quite_time"]

  def setUp(self):
    self.default_targets = [self.CORRIDOR_ECHO]
    self.text = "Test text."

    args = {
        "env": self.env,
        "quite_time": self.quite_time,
        "rules": self.rules,
    }
    self.alexa = tts.Alexa(mock.Mock(), mock.Mock(), mock.MagicMock(), args,
                           mock.Mock(), mock.Mock(), mock.Mock())
    self.alexa.initialize()

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

  @staticmethod
  def _target_for(area):
    return f"media_player.{area}_echo"


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


class TestTargets(TestBase):
  """Default targets tests."""

  def _test_not_played(self, targets):
    """Assert text was not played on the default targets."""

    expected_targets = self.alexa.tts(text=self.text, silent_in=targets)
    for target in targets:
      self.assertNotIn(
          target,
          expected_targets,
          f"Should not play on the default target ({target}) if silenced.",
      )
      self._assert_hass_not_called()

  def _test_played(self, areas, silent_in=None):
    """Assert text was played on the default target."""

    expected_targets = self.alexa.tts(text=self.text, silent_in=silent_in)

    for area in areas:
      target = self._target_for(area)
      self.assertIn(
          target,
          expected_targets,
          f"Should play on the default target in {area}.",
      )

    for area in silent_in or ():
      target = self._target_for(area)
      self.assertNotIn(
          target,
          expected_targets,
          f"Should not play on the target in {area} if silenced.",
      )

    self._assert_hass_called_with(self.text, expected_targets)


class TestPlayDefaultTargetsNormalTime(TestTargets):
  """Default targets normal time tests."""

  def test_not_played(self):
    play_default = [TestBase.OFFICE_1, TestBase.OFFICE_2]
    with mock.patch.dict(self.alexa.env,
                         {"play_default": {
                             "normal_time": play_default
                         }}):
      super()._test_not_played(play_default)

    # Test current targets.
    super()._test_not_played(self.env["play_default"]["normal_time"])

  def test_played(self):
    play_default = (TestBase.OFFICE_1, TestBase.OFFICE_2)
    with mock.patch.dict(self.alexa.env,
                         {"play_default": {
                             "normal_time": play_default
                         }}):
      super()._test_played(play_default)

    # Test current targets.
    super()._test_played(self.env["play_default"]["normal_time"])


class TestPlayDefaultTargetsQuiteTime(TestTargets):
  """Default targets quite time tests."""

  play_default = (TestBase.OFFICE_1, TestBase.OFFICE_2)
  env_patch = {
      "play_always": {
          "quite_time": []
      },
      "play_default": {
          "quite_time": play_default
      }
  }

  def test_not_played(self):
    self.alexa.get_state.side_effect = lambda sensor: {
        self.alexa.quite_time: tts.Alexa.STATE_ON
    }.get(sensor, tts.Alexa.STATE_OFF)
    with mock.patch.dict(self.alexa.env, self.env_patch):
      super()._test_not_played(self.play_default)

    # Test current targets.
    super()._test_not_played(self.env["play_default"]["quite_time"])

  def test_played(self):
    self.alexa.get_state.side_effect = lambda sensor: {
        self.quite_time: tts.Alexa.STATE_ON
    }.get(sensor, tts.Alexa.STATE_OFF)
    with mock.patch.dict(self.alexa.env, self.env_patch):
      super()._test_played(self.play_default)

    # Test current targets.
    super()._test_played(self.env["play_default"]["quite_time"])


class TestPlayAlwaysTargetsNormalTime(TestTargets):
  """Last resort targets normal time tests."""

  play_always = [TestBase.OFFICE_1, TestBase.OFFICE_2]
  env_patch = {
      "play_always": {
          "normal_time": play_always
      },
      "play_default": {
          "normal_time": []
      }
  }

  def test_not_played(self):
    with mock.patch.dict(self.alexa.env, self.env_patch):
      super()._test_not_played(self.play_always)

    # Test current targets.
    super()._test_not_played(self.env["play_always"]["normal_time"])

  def test_played(self):
    with mock.patch.dict(self.alexa.env, self.env_patch):
      super()._test_played(self.play_always)

    self.alexa.get_state.side_effect = lambda sensor: {
        TestBase.LIVING_ROOM_MOTION: tts.Alexa.STATE_ON
    }.get(sensor, tts.Alexa.STATE_OFF)
    super()._test_played(self.env["play_always"]["normal_time"],
                         silent_in=[TestBase.LIVING_ROOM])

    # Test current targets.
    super()._test_played(self.env["play_always"]["normal_time"])


class TestTarget(TestBase):
  """A base class for specific target behavior tests."""

  def _test_not_played_normal_time(self, area, conditions):
    """Assert text was not played on the target during normal time. """

    with mock.patch.dict(self.alexa.rules, self.rules):
      for condition in conditions:
        self.alexa.get_state.side_effect = lambda sensor: {
            condition: tts.Alexa.STATE_ON
        }.get(sensor, tts.Alexa.STATE_OFF)

        target = self._target_for(area)
        targets = self.alexa.tts(text=self.text, silent_in=[area])
        self.assertNotIn(
            target,
            targets,
            f"Should not play in the {area} if silenced and "
            f"{conditions[condition]}.",
        )
        self._assert_hass_called_with(self.text, targets)

  def _test_played_normal_time(self, area, conditions):
    """Assert text was played on the target during normal time."""

    target = self._target_for(area)
    expected_targets = [target]

    with mock.patch.dict(self.alexa.rules,
                         {area: {
                             "conditions": conditions,
                             "target": target
                         }}):
      for condition in conditions:
        self.alexa.get_state.side_effect = lambda sensor: {
            condition: tts.Alexa.STATE_ON
        }.get(sensor, tts.Alexa.STATE_OFF)

        targets = self.alexa.tts(text=self.text)

        self.assertEqual(
            targets,
            expected_targets,
            f"Should play in the {area} if {conditions[condition]}.",
        )
        self._assert_hass_called_with(self.text, expected_targets)

  def _test_not_played_quite_time(self, area, conditions):
    """Assert text was not played on the target during quite time."""

    with mock.patch.dict(self.alexa.env,
                         {"play_always": {
                             "quite_time": [area]
                         }}):

      for condition in conditions:
        self.alexa.get_state.side_effect = lambda sensor: {
            condition: tts.Alexa.STATE_ON,
            self.quite_time: tts.Alexa.STATE_ON
        }.get(sensor, tts.Alexa.STATE_OFF)

        expected_targets = self.alexa.tts(text=self.text, silent_in=[area])

        self.assertNotIn(
            self._target_for(area),
            expected_targets,
            f"Should not play in the {area} during quite time if silenced.",
        )
        self._assert_hass_not_called()

  def _test_played_if_not(self, area, conditions, if_not):
    """
    Assert text was not played on the target due to unless rule conditions.
    """

    condition_dict = {}
    for condition in tuple(conditions.keys()) + if_not["conditions"]:
      condition_dict[condition] = tts.Alexa.STATE_ON

    self.alexa.get_state.side_effect = lambda sensor: condition_dict.get(
        sensor, tts.Alexa.STATE_OFF)

    target = self._target_for(area)
    targets = self.alexa.tts(text=self.text)

    self.assertNotIn(
        target,
        targets,
        f"Should not play in the {area} when {if_not['description']}.",
    )
    self._assert_hass_called_with(self.text, targets)

  def _test_played_quite_time(self, area):
    """Assert text was played on the target during quite time. """

    self.alexa.get_state.side_effect = lambda sensor: {
        self.alexa.quite_time: tts.Alexa.STATE_ON
    }.get(sensor, tts.Alexa.STATE_OFF)

    with mock.patch.dict(self.alexa.env,
                         {"play_always": {
                             "quite_time": [area]
                         }}):
      expected_targets = self.alexa.tts(text=self.text)

      self.assertIn(
          self._target_for(area),
          expected_targets,
          f"Should play in the {area} during quite time.",
      )
      self._assert_hass_called_with(self.text, expected_targets)


class TestBathroom1(TestTarget):
  """Bathroom 1 tests."""

  conditions = {
      TestBase.BATHROOM_1_LIGHT: "the light is on",
      TestBase.BATHROOM_1_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.BATHROOM_1, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.BATHROOM_1, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.BATHROOM_1, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.BATHROOM_1)

  def test_played_if_not(self):
    if_not = {
        "conditions": (TestBase.BATHROOM_1_DOOR, TestBase.BEDROOM_1_LIGHT),
        "description":
            f"playing in {TestBase.BEDROOM_1} and {TestBase.BATHROOM_1} door is open"
    }

    super()._test_played_if_not(TestBase.BATHROOM_1, self.conditions, if_not)


class TestBathroom2(TestTarget):
  """Bathroom 2 tests."""

  conditions = {
      TestBase.BATHROOM_2_LIGHT: "the light is on",
      TestBase.BATHROOM_2_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.BATHROOM_2, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.BATHROOM_2, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(
        TestBase.BATHROOM_2,
        self.conditions,
    )

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.BATHROOM_2)

  def test_played_if_not(self):
    if_not = {
        "conditions": (TestBase.BATHROOM_2_DOOR, TestBase.LIVING_ROOM_LIGHT),
        "description":
            f"playing in {TestBase.LIVING_ROOM} and {TestBase.BATHROOM_2} door is open"
    }

    super()._test_played_if_not(TestBase.BATHROOM_2, self.conditions, if_not)


class TestBedroom1(TestTarget):
  """Bedroom 1 tests."""

  conditions = {
      TestBase.BEDROOM_1_LIGHT: "the light is on",
      TestBase.BEDROOM_1_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.BEDROOM_1, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.BEDROOM_1, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.BEDROOM_1, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.BEDROOM_1)


class TestGarage(TestTarget):
  """Garage tests."""

  conditions = {
      TestBase.GARAGE_LIGHT: "the light is on",
      TestBase.GARAGE_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.GARAGE, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.GARAGE, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.GARAGE, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.GARAGE)


class TestLivingRoom(TestTarget):
  """Living room tests."""

  conditions = {
      TestBase.DINING_AREA_LIGHT:
          "the dining area light is on",
      TestBase.HALLWAY_MOTION:
          "there was a recent motion in the hallway",
      TestBase.KITCHEN_LIGHT:
          "the kitchen light is on",
      TestBase.KITCHEN_MOTION:
          "there was a recent motion in the kitchen",
      TestBase.LIVING_ROOM_LIGHT:
          "the living room light is on",
      TestBase.LIVING_ROOM_MOTION:
          "there was a recent motion in the living room",
      TestBase.LIVING_ROOM_TV:
          "the living room TV is on",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.LIVING_ROOM, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.LIVING_ROOM, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.LIVING_ROOM, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.LIVING_ROOM)


class TestOffice1(TestTarget):
  """Office1 tests."""

  conditions = {
      TestBase.OFFICE_1_LIGHT: "the light is on",
      TestBase.OFFICE_1_MOTION: "there was a recent motion",
      TestBase.OFFICE_1_TV: "the TV is on",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.OFFICE_1, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.OFFICE_1, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.OFFICE_1, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.OFFICE_1)

  def test_played_if_not(self):
    if_not = {
        "conditions": (TestBase.DINING_AREA_LIGHT, TestBase.KITCHEN_LIGHT,
                       TestBase.LIVING_ROOM_LIGHT, TestBase.LIVING_ROOM_TV),
        "description": f"playing in {TestBase.LIVING_ROOM}"
    }

    super()._test_played_if_not(TestBase.OFFICE_1, self.conditions, if_not)


class TestOffice2(TestTarget):
  """Office2 tests."""

  conditions = {
      TestBase.OFFICE_2_LIGHT: "the light is on",
      TestBase.OFFICE_2_MOTION: "there was a recent motion",
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.OFFICE_2, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.OFFICE_2, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.OFFICE_2, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.OFFICE_2)


if __name__ == "__main__":
  unittest.main()
