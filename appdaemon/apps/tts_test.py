"""Tests for tts.py"""

__author__ = 'Ark (ark@cho.red)'

# pylint: disable=cell-var-from-loop
# pylint: disable=missing-function-docstring

import unittest
from unittest import mock

import yaml  # pylint: disable=import-error

import tts


class TestBase(unittest.TestCase):
  """A base class for tests."""

  BATHROOM_1 = 'bathroom_1'
  BATHROOM_1_DOOR = 'binary_sensor.bathroom_1_door'
  BATHROOM_1_ECHO = 'media_player.bathroom_1_echo'
  BATHROOM_1_LIGHT = 'binary_sensor.bathroom_1_lights'
  BATHROOM_1_MOTION = 'binary_sensor.bathroom_1_motion_5m'

  BATHROOM_2 = 'bathroom_2'
  BATHROOM_2_DOOR = 'binary_sensor.bathroom_2_door'
  BATHROOM_2_ECHO = 'media_player.bathroom_2_echo'
  BATHROOM_2_LIGHT = 'binary_sensor.bathroom_2_lights'
  BATHROOM_2_MOTION = 'binary_sensor.bathroom_2_motion_5m'

  BATHROOM_3 = 'bathroom_3'
  BATHROOM_3_DOOR = 'binary_sensor.bathroom_3_door'
  BATHROOM_3_ECHO = 'media_player.bathroom_3_echo'
  BATHROOM_3_LIGHT = 'binary_sensor.bathroom_3_lights'
  BATHROOM_3_MOTION = 'binary_sensor.bathroom_3_motion_5m'

  BEDROOM_1 = 'bedroom_1'
  BEDROOM_1_ECHO = 'media_player.bedroom_1_echo'
  BEDROOM_1_LIGHT = 'binary_sensor.bedroom_1_lights'
  BEDROOM_1_MOTION = 'binary_sensor.bedroom_1_motion_5m'

  DEN = 'den'
  DEN_ECHO = 'media_player.den_echo'
  DEN_LIGHT = 'binary_sensor.den_lights'
  DEN_MOTION = 'binary_sensor.den_motion_5m'

  DINING_AREA_LIGHT = 'binary_sensor.dining_area_lights'

  GARAGE = 'garage'
  GARAGE_ECHO = 'media_player.garage_echo'
  GARAGE_LIGHT = 'binary_sensor.garage_lights'
  GARAGE_MOTION = 'binary_sensor.garage_motion_5m'

  GREAT_ROOM = 'great_room'
  GREAT_ROOM_ECHO = 'media_player.great_room_echo'
  GREAT_ROOM_LIGHT = 'binary_sensor.great_room_lights'
  GREAT_ROOM_MOTION = 'binary_sensor.great_room_motion_5m'
  GREAT_ROOM_TV = 'binary_sensor.great_room_tv'

  HALLWAY_MOTION = 'binary_sensors.hallway_motion'

  KITCHEN_LIGHT = 'binary_sensor.kitchen_lights'
  KITCHEN_MOTION = 'binary_sensor.kitchen_motion_5m'
  KITCHEN_TV = 'media_player.kitchen_tv'

  OFFICE_1 = 'office_1'
  OFFICE_1_ECHO = 'media_player.office_1_echo'
  OFFICE_1_ECHO_DND_MODE = 'media_player.office_1_echo_do_not_disturb_switch'
  OFFICE_1_LIGHT = 'binary_sensor.office_1_light'
  OFFICE_1_MOTION = 'binary_sensor.office_1_motion_5m'
  OFFICE_1_TV = 'remote.office_1_tv'

  OFFICE_2 = 'office_2'
  OFFICE_2_ECHO = 'media_player.office_2_echo'
  OFFICE_2_LIGHT = 'binary_sensor.office_2_lights'
  OFFICE_2_MOTION = 'binary_sensor.office_2_motion_5m'

  STAIRWAY = 'stairway'
  STAIRWAY_ECHO = 'media_player.stairway_echo'

  @classmethod
  def setUpClass(cls):
    with open('apps.yaml', 'r', encoding='utf-8') as config_file:
      config = yaml.safe_load(config_file)['tts']

    cls.env = config['env']
    cls.env.update({
        'play_always': {
            'normal_time': [],
            'quite_time': [],
        },
        'play_default': {
            'normal_time': [],
            'quite_time': [],
        }
    })
    cls.rules = config['rules']
    cls.quite_time = config['quite_time']

  def setUp(self):
    self.text = 'Test text'

    args = {
        'env': self.env,
        'quite_time': self.quite_time,
        'rules': self.rules,
    }
    self.amazon_echo = tts.AmazonEcho(mock.Mock(), mock.Mock(),
                                      mock.MagicMock(), args, mock.Mock(),
                                      mock.Mock(), mock.Mock())
    self.amazon_echo.initialize()

    tts.AmazonEcho.call_service = mock.Mock()
    tts.AmazonEcho.get_state = mock.Mock()

  def _assert_hass_called_with(self, text, targets):
    self.amazon_echo.call_service.assert_called_with('notify/alexa_media',
                                                     target=targets,
                                                     message=text,
                                                     data={'type': 'tts'})

  def _assert_hass_called_with_defaults(self):
    return self._assert_hass_called_with(
        self.text, self.env['play_default']['normal_time'])

  def _assert_hass_not_called(self):
    self.amazon_echo.call_service.assert_not_called()


class TestArgs(TestBase):
  """Test input args."""

  def test_no_text_raises_value_error(self):
    """Test no text handler."""

    with self.assertRaises(ValueError) as ctx:
      self.amazon_echo.tts()
    self.assertIn('Text is required', str(ctx.exception))

    with self.assertRaises(ValueError) as ctx:
      self.amazon_echo.tts(text='')
    self.assertIn("Text mustn't be empty", str(ctx.exception))

  def test_areas_off_areas_on_wildcard_conflict(self):
    with self.assertRaises(ValueError) as ctx:
      self.amazon_echo.tts(text=self.text, areas_off='*', areas_on='*')
    self.assertIn(
        "You can't use wildcard targets for both areas_off and areas_on at "
        "the same time", str(ctx.exception))

  def test_area_off_wildcard_play_always(self):
    env_patch = {'play_always': {'normal_time': [TestBase.STAIRWAY]}}

    with mock.patch.dict(self.amazon_echo.env, env_patch):
      expected_targets = self.amazon_echo.tts(text=self.text, areas_off='*')
      self.assertListEqual(expected_targets, [])

  def test_area_off_wildcard_play_default(self):
    env_patch = {'play_default': {'normal_time': [TestBase.GREAT_ROOM]}}

    with mock.patch.dict(self.amazon_echo.env, env_patch):
      expected_targets = self.amazon_echo.tts(text=self.text, areas_off='*')
      self.assertListEqual(expected_targets, [])


class TestTargetAreaBase(TestBase):
  """Target area test base."""

  def _test_not_played(self, expected_areas, areas_off=None, areas_on=None):
    """Assert was not played on the targets."""

    expected_targets = self.amazon_echo.tts(text=self.text,
                                            areas_off=areas_off,
                                            areas_on=areas_on)
    for area in areas_off or ():
      target = self.amazon_echo.get_target(area)
      self.assertNotIn(
          target,
          expected_targets,
          f'Should not play in the {area} ({target}) if silenced.',
      )

    for area in expected_areas:
      target = self.amazon_echo.get_target(area)
      self.assertIn(
          target,
          expected_targets,
          f'Should play in the {area} ({target}) if not silenced.',
      )

  def _test_played(self, expected_areas, areas_off=None, areas_on=None):
    """Assert played on the target."""

    expected_targets = self.amazon_echo.tts(text=self.text,
                                            areas_off=areas_off,
                                            areas_on=areas_on)

    for area in expected_areas:
      target = self.amazon_echo.get_target(area)
      self.assertIn(
          target,
          expected_targets,
          f"Should play in the {area} ({target}).",
      )

    self._assert_hass_called_with(self.text, expected_targets)


class TestConflictingAreasTargets(TestTargetAreaBase):
  """Conflicting areas_off/areas_on targets tests."""

  areas_off = (TestBase.OFFICE_2, TestBase.BATHROOM_2)
  areas_on = (TestBase.BATHROOM_1, TestBase.BATHROOM_2)
  env_patch = {
      'play_always': {
          'normal_time': [],
          'quite_time': [],
      },
      'play_default': {
          'normal_time': [],
          'quite_time': [],
      }
  }

  def test_not_played(self):
    with mock.patch.dict(self.amazon_echo.env, self.env_patch):
      super()._test_not_played(set(self.areas_on).difference(self.areas_off),
                               areas_off=self.areas_off,
                               areas_on=self.areas_on)

  def test_played(self):
    with mock.patch.dict(self.amazon_echo.env, self.env_patch):
      super()._test_played(set(self.areas_on).difference(self.areas_off),
                           areas_off=self.areas_off,
                           areas_on=self.areas_on)


class TestPlayAlwaysAndPlayDefaultTargets(TestTargetAreaBase):
  """Play always and play default mixed together tests."""

  play_always = (TestBase.OFFICE_1, TestBase.OFFICE_2)
  play_default = (TestBase.BATHROOM_1, TestBase.BATHROOM_2)

  env_patch_normal_time = {
      'play_always': {
          'normal_time': play_always,
          'quite_time': [],
      },
      'play_default': {
          'normal_time': play_default,
          'quite_time': [],
      }
  }

  env_patch_quite_time = {
      'play_always': {
          'normal_time': [],
          'quite_time': play_always,
      },
      'play_default': {
          'normal_time': [],
          'quite_time': play_default,
      }
  }

  def test_not_played(self):
    # Normal time.
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_normal_time):
      super()._test_not_played((), areas_off=self.play_always)
      super()._test_not_played((), areas_off=self.play_default)

      self.amazon_echo.get_state.side_effect = lambda sensor: {
          TestBase.GREAT_ROOM_MOTION: tts.AmazonEcho.STATE_ON
      }.get(sensor, tts.AmazonEcho.STATE_OFF)
      super()._test_not_played(
          set(self.play_always).union((TestBase.GREAT_ROOM,)))
      super()._test_not_played((TestBase.GREAT_ROOM,),
                               areas_off=self.play_always)
      super()._test_not_played((TestBase.GREAT_ROOM,))

    # Quite time.
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_quite_time):
      self.amazon_echo.get_state.side_effect = lambda sensor: {
          self.amazon_echo.quite_time: tts.AmazonEcho.STATE_ON
      }.get(sensor, tts.AmazonEcho.STATE_OFF)

      super()._test_not_played((), areas_off=self.play_always)
      super()._test_not_played((), areas_off=self.play_default)

      self.amazon_echo.get_state.side_effect = lambda sensor: {
          self.amazon_echo.quite_time: tts.AmazonEcho.STATE_ON,
          TestBase.GREAT_ROOM_MOTION: tts.AmazonEcho.STATE_ON
      }.get(sensor, tts.AmazonEcho.STATE_OFF)

      super()._test_not_played(set(self.play_always))
      super()._test_not_played((), areas_off=self.play_always)
      super()._test_not_played((), areas_off=self.play_default)

  def test_played(self):
    # Normal time.
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_normal_time):
      super()._test_played(self.play_always)

    # Quite time.
    self.amazon_echo.get_state.side_effect = lambda sensor: {
        self.quite_time: tts.AmazonEcho.STATE_ON
    }.get(sensor, tts.AmazonEcho.STATE_OFF)
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_quite_time):
      super()._test_played(self.play_always)


class TestPlayAlwaysTargets(TestTargetAreaBase):
  """Play always targets tests."""

  areas = (TestBase.OFFICE_1, TestBase.OFFICE_2)
  env_patch_normal_time = {
      'play_always': {
          'normal_time': areas,
          'quite_time': [],
      },
      'play_default': {
          'normal_time': [],
          'quite_time': [],
      }
  }
  env_patch_quite_time = {
      'play_always': {
          'normal_time': [],
          'quite_time': areas,
      },
      'play_default': {
          'normal_time': [],
          'quite_time': [],
      }
  }

  def test_not_played(self):
    # Normal time.
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_normal_time):
      super()._test_not_played((), areas_off=self.areas)

    # Quite time.
    self.amazon_echo.get_state.side_effect = lambda sensor: {
        self.amazon_echo.quite_time: tts.AmazonEcho.STATE_ON
    }.get(sensor, tts.AmazonEcho.STATE_OFF)
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_quite_time):
      super()._test_not_played((), areas_off=self.areas)

  def test_played(self):
    # Normal time.
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_normal_time):
      super()._test_played(self.areas)

    # Quite time.
    self.amazon_echo.get_state.side_effect = lambda sensor: {
        self.quite_time: tts.AmazonEcho.STATE_ON
    }.get(sensor, tts.AmazonEcho.STATE_OFF)
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_quite_time):
      super()._test_played(self.areas)


class TestPlayDefaultTargets(TestTargetAreaBase):
  """Play default targets tests."""

  areas = (TestBase.OFFICE_1, TestBase.OFFICE_2)
  env_patch_normal_time = {
      'play_always': {
          'normal_time': [],
          'quite_time': [],
      },
      'play_default': {
          'normal_time': areas,
          'quite_time': [],
      }
  }
  env_patch_quite_time = {
      'play_always': {
          'normal_time': [],
          'quite_time': [],
      },
      'play_default': {
          'normal_time': [],
          'quite_time': areas,
      }
  }

  def test_not_played(self):
    # Normal time.
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_normal_time):
      super()._test_not_played((), areas_off=self.areas)

    # Quite time.
    self.amazon_echo.get_state.side_effect = lambda sensor: {
        self.amazon_echo.quite_time: tts.AmazonEcho.STATE_ON
    }.get(sensor, tts.AmazonEcho.STATE_OFF)
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_quite_time):
      super()._test_not_played((), areas_off=self.areas)

  def test_played(self):
    # Normal time.
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_normal_time):
      super()._test_played(self.areas)

    # Quite time.
    self.amazon_echo.get_state.side_effect = lambda sensor: {
        self.quite_time: tts.AmazonEcho.STATE_ON
    }.get(sensor, tts.AmazonEcho.STATE_OFF)
    with mock.patch.dict(self.amazon_echo.env, self.env_patch_quite_time):
      super()._test_played(self.areas)


class TestTargetConditionBase(TestBase):
  """A base class for specific target behavior tests."""

  env_patch = {
      'play_default': {
          'normal_time': [TestBase.STAIRWAY],
          'quite_time': [],
      }
  }

  def _test_not_played_normal_time(self, area, conditions):
    """Assert text was not played on the target during normal time. """
    with mock.patch.dict(self.amazon_echo.env, self.env_patch):
      with mock.patch.dict(self.amazon_echo.rules, self.rules):
        for condition in conditions:
          self.amazon_echo.get_state.side_effect = lambda sensor: {
              condition: tts.AmazonEcho.STATE_ON
          }.get(sensor, tts.AmazonEcho.STATE_OFF)

          target = self.amazon_echo.get_target(area)
          targets = self.amazon_echo.tts(text=self.text, areas_off=[area])
          self.assertNotIn(
              target,
              targets,
              f'Should not play in the {area} if silenced and '
              f'{conditions[condition]}.',
          )
          self._assert_hass_called_with(self.text, targets)

  def _test_played_normal_time(self, area, conditions):
    """Assert text was played on the target during normal time."""

    target = self.amazon_echo.get_target(area)
    expected_targets = [target]

    with mock.patch.dict(self.amazon_echo.rules,
                         {area: {
                             'conditions': conditions,
                             'target': target
                         }}):
      for condition in conditions:
        self.amazon_echo.get_state.side_effect = lambda sensor: {
            condition: tts.AmazonEcho.STATE_ON
        }.get(sensor, tts.AmazonEcho.STATE_OFF)

        targets = self.amazon_echo.tts(text=self.text)

        self.assertEqual(
            targets,
            expected_targets,
            f'Should play in the {area} if {conditions[condition]}.',
        )
        self._assert_hass_called_with(self.text, expected_targets)

  def _test_not_played_quite_time(self, area, conditions):
    """Assert text was not played on the target during quite time."""

    with mock.patch.dict(self.amazon_echo.env,
                         {'play_always': {
                             'quite_time': [area]
                         }}):

      for condition in conditions:
        self.amazon_echo.get_state.side_effect = lambda sensor: {
            condition: tts.AmazonEcho.STATE_ON,
            self.quite_time: tts.AmazonEcho.STATE_ON
        }.get(sensor, tts.AmazonEcho.STATE_OFF)

        expected_targets = self.amazon_echo.tts(text=self.text,
                                                areas_off=[area])

        self.assertNotIn(
            self.amazon_echo.get_target(area),
            expected_targets,
            f"Should not play in the {area} during quite time if silenced.",
        )
        self._assert_hass_not_called()

  def _test_played_if_not(self, area, conditions, if_not):
    """
    Assert text was not played on the target due to unless rule conditions.
    """

    condition_dict = {}
    for condition in tuple(conditions.keys()) + if_not['conditions']:
      condition_dict[condition] = tts.AmazonEcho.STATE_ON

    self.amazon_echo.get_state.side_effect = lambda sensor: condition_dict.get(
        sensor, tts.AmazonEcho.STATE_OFF)

    target = self.amazon_echo.get_target(area)
    targets = self.amazon_echo.tts(text=self.text)

    self.assertNotIn(
        target,
        targets,
        f'Should not play in the {area} when {if_not["description"]}.',
    )
    self._assert_hass_called_with(self.text, targets)

  def _test_played_quite_time(self, area):
    """Assert text was played on the target during quite time. """

    self.amazon_echo.get_state.side_effect = lambda sensor: {
        self.amazon_echo.quite_time: tts.AmazonEcho.STATE_ON
    }.get(sensor, tts.AmazonEcho.STATE_OFF)

    with mock.patch.dict(self.amazon_echo.env,
                         {'play_always': {
                             'quite_time': [area]
                         }}):
      expected_targets = self.amazon_echo.tts(text=self.text)

      self.assertIn(
          self.amazon_echo.get_target(area),
          expected_targets,
          f'Should play in the {area} during quite time.',
      )
      self._assert_hass_called_with(self.text, expected_targets)


class TestBathroom1(TestTargetConditionBase):
  """Bathroom 1 tests."""

  conditions = {
      TestBase.BATHROOM_1_LIGHT: 'the light is on',
      TestBase.BATHROOM_1_MOTION: 'there was a recent motion',
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
        'conditions': (TestBase.BATHROOM_1_DOOR, TestBase.BEDROOM_1_LIGHT),
        'description':
            f'playing in {TestBase.BEDROOM_1} and {TestBase.BATHROOM_1} door is open'
    }

    super()._test_played_if_not(TestBase.BATHROOM_1, self.conditions, if_not)


class TestBathroom2(TestTargetConditionBase):
  """Bathroom 2 tests."""

  conditions = {
      TestBase.BATHROOM_2_LIGHT: 'the light is on',
      TestBase.BATHROOM_2_MOTION: 'there was a recent motion',
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


class TestBathroom3(TestTargetConditionBase):
  """Bathroom 3 tests."""

  conditions = {
      TestBase.BATHROOM_3_LIGHT: 'the light is on',
      TestBase.BATHROOM_3_MOTION: 'there was a recent motion',
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.BATHROOM_3, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.BATHROOM_3, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(
        TestBase.BATHROOM_3,
        self.conditions,
    )

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.BATHROOM_3)


class TestBedroom1(TestTargetConditionBase):
  """Bedroom 1 tests."""

  conditions = {
      TestBase.BEDROOM_1_LIGHT: 'the light is on',
      TestBase.BEDROOM_1_MOTION: 'there was a recent motion',
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.BEDROOM_1, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.BEDROOM_1, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.BEDROOM_1, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.BEDROOM_1)


class TestDen(TestTargetConditionBase):
  """Den tests."""

  conditions = {
      TestBase.DEN_LIGHT: 'the light is on',
      TestBase.DEN_MOTION: 'there was a recent motion',
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.DEN, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.DEN, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.DEN, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.DEN)


class TestGarage(TestTargetConditionBase):
  """Garage tests."""

  conditions = {
      TestBase.GARAGE_LIGHT: 'the light is on',
      TestBase.GARAGE_MOTION: 'there was a recent motion',
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.GARAGE, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.GARAGE, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.GARAGE, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.GARAGE)


class TestGreatRoom(TestTargetConditionBase):
  """Great room tests."""

  conditions = {
      TestBase.DINING_AREA_LIGHT: 'the dining area light is on',
      TestBase.GREAT_ROOM_LIGHT: 'the great room light is on',
      TestBase.GREAT_ROOM_MOTION: 'there was a recent motion in the great room',
      TestBase.GREAT_ROOM_TV: 'the great room TV is on',
      TestBase.HALLWAY_MOTION: 'there was a recent motion in the hallway',
      TestBase.KITCHEN_LIGHT: 'the kitchen light is on',
      TestBase.KITCHEN_MOTION: 'there was a recent motion in the kitchen',
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.GREAT_ROOM, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.GREAT_ROOM, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.GREAT_ROOM, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.GREAT_ROOM)


class TestOffice1(TestTargetConditionBase):
  """Office1 tests."""

  conditions = {
      TestBase.OFFICE_1_LIGHT: 'the light is on',
      TestBase.OFFICE_1_MOTION: 'there was a recent motion',
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.OFFICE_1, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.OFFICE_1, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.OFFICE_1, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.OFFICE_1)

  def test_not_played_in_dnd_mode(self):
    conditions = {
        TestBase.OFFICE_1_ECHO_DND_MODE: 'office_1 echo in DND mode',
    }
    super()._test_not_played_normal_time(TestBase.OFFICE_1, conditions)


class TestOffice2(TestTargetConditionBase):
  """Office2 tests."""

  conditions = {
      TestBase.OFFICE_2_LIGHT: 'the light is on',
      TestBase.OFFICE_2_MOTION: 'there was a recent motion',
  }

  def test_not_played_normal_time(self):
    super()._test_not_played_normal_time(TestBase.OFFICE_2, self.conditions)

  def test_not_played_quite_time(self):
    super()._test_not_played_quite_time(TestBase.OFFICE_2, self.conditions)

  def test_played_normal_time(self):
    super()._test_played_normal_time(TestBase.OFFICE_2, self.conditions)

  def test_played_quite_time(self):
    super()._test_played_quite_time(TestBase.OFFICE_2)


if __name__ == '__main__':
  unittest.main()
