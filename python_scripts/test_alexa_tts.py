"""Tests for alexa_announcement.py"""

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
                "data": {"type": "tts"},
                "message": message,
                "target": targets,
            },
        )

    def _assert_hass_called_with_defaults(self):
        return self._assert_hass_called_with(self.test_message, self.default_targets)


class TestArgs(unittest.TestCase):
    """Test input args."""

    def test_no_message__raises_value_error(self):
        """Test no message handler."""

        with self.assertRaises(ValueError) as ctx:
            alexa_tts.make_announcement({})

            self.assertIn("Message is required", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            alexa_tts.make_announcement({}, message="")

            self.assertIn("Message is required", str(ctx.exception))


class TestDefaults(TestBase):
    """Test default behavior."""

    def test_defaults(self):
        expected_targets = alexa_tts.make_announcement(
            self.hass, message=self.test_message
        )

        self.assertEqual(self.default_targets, expected_targets)
        self._assert_hass_called_with_defaults()


class TestArea(TestBase):
    """A base class for specific area behavior."""

    def _test_announced(self, area_name, area_device, area_cases):
        expected_targets = [area_device]

        for case in area_cases:
            with mock.patch.dict(self.hass.states, {case: self.sensor_on}):
                targets = alexa_tts.make_announcement(
                    self.hass, message=self.test_message
                )

                self.assertEqual(
                    targets,
                    expected_targets,
                    f"Should announce in the {area_name} {area_cases[case]}.",
                )
                self._assert_hass_called_with(self.test_message, expected_targets)

    def _test_not_announced(self, area_name, area_device):
        expected_targets = alexa_tts.make_announcement(
            self.hass, message=self.test_message, silent_in=[area_device]
        )

        self.assertNotIn(
            area_device,
            expected_targets,
            f"Should not announce in the {area_name} if silenced.",
        )
        self._assert_hass_called_with(self.test_message, expected_targets)


class TestGarage(TestArea):
    """Garage tests."""

    def test_not_announced(self):
        super()._test_not_announced(alexa_tts.GARAGE, alexa_tts.GARAGE_ECHO)

    def test_announced(self):
        super()._test_announced(
            alexa_tts.GARAGE,
            alexa_tts.GARAGE_ECHO,
            {
                alexa_tts.GARAGE_LIGHT: "when the light is on",
                alexa_tts.GARAGE_MOTION: "when there was a recent motion",
            },
        )


class TestLivingRoom(TestArea):
    """Living room tests."""

    def test_announced(self):
        super()._test_announced(
            alexa_tts.LIVING_ROOM,
            alexa_tts.LIVING_ROOM_ECHO,
            {
                alexa_tts.DINING_AREA_LIGHT: "when the dining area light is on",
                alexa_tts.HALLWAY_MOTION: "when there was a recent motion in the hallway",
                alexa_tts.KITCHEN_LIGHT: "when the kitchen light is on",
                alexa_tts.KITCHEN_MOTION: "when there was a recent motion in the kitchen",
                alexa_tts.LIVING_ROOM_LIGHT: "when the living room light is on",
                alexa_tts.LIVING_ROOM_MOTION: "when there was a recent motion in the living room",
                alexa_tts.LIVING_ROOM_TV: "when the living room TV is on",
            },
        )

    def test_not_announced(self):
        super()._test_not_announced(alexa_tts.LIVING_ROOM, alexa_tts.LIVING_ROOM_ECHO)


class TestOffice1(TestArea):
    """Office1 tests."""

    def test_announced(self):
        super()._test_announced(
            alexa_tts.OFFICE_1,
            alexa_tts.OFFICE_1_ECHO,
            {
                alexa_tts.OFFICE_1_LIGHT: "when the light is on",
                alexa_tts.OFFICE_1_MOTION: "when there was a recent motion",
                alexa_tts.OFFICE_1_TV: "when the TV is on",
            },
        )

    def test_not_announced(self):
        super()._test_not_announced(alexa_tts.OFFICE_1, alexa_tts.OFFICE_1_ECHO)


class TestOffice2(TestArea):
    """Office2 tests."""

    def test_announced(self):
        super()._test_announced(
            alexa_tts.OFFICE_2,
            alexa_tts.OFFICE_2_ECHO,
            {
                alexa_tts.OFFICE_2_LIGHT: "when the light is on",
                alexa_tts.OFFICE_2_MOTION: "when there was a recent motion",
            },
        )

    def test_not_announced(self):
        super()._test_not_announced(alexa_tts.OFFICE_2, alexa_tts.OFFICE_2_ECHO)


class TestPrimaryBathroom(TestArea):
    """Primary bedroom tests."""

    def test_announced(self):
        super()._test_announced(
            alexa_tts.PRIMARY_BATHROOM,
            alexa_tts.PRIMARY_BATHROOM_ECHO,
            {
                alexa_tts.PRIMARY_BATHROOM_LIGHT: "when the light is on",
                alexa_tts.PRIMARY_BATHROOM_MOTION: "when there was a recent motion",
            },
        )

    def test_not_announced(self):
        super()._test_not_announced(
            alexa_tts.PRIMARY_BATHROOM, alexa_tts.PRIMARY_BATHROOM_ECHO
        )


class TestPrimaryBedroom(TestArea):
    """Primary bedroom tests."""

    def test_announced(self):
        super()._test_announced(
            alexa_tts.PRIMARY_BEDROOM,
            alexa_tts.PRIMARY_BEDROOM_ECHO,
            {
                alexa_tts.QUITE_TIME: "during quite hours",
                alexa_tts.PRIMARY_BEDROOM_LIGHT: "when the light is on",
                alexa_tts.PRIMARY_BEDROOM_MOTION: "when there was a recent motion",
            },
        )

    def test_not_announced(self):
        super()._test_not_announced(
            alexa_tts.PRIMARY_BEDROOM, alexa_tts.PRIMARY_BEDROOM_ECHO
        )

    def test_not_announced__quite_hours(self):
        expected_targets = []

        with mock.patch.dict(
            self.hass.states, {"binary_sensor.is_quite_time": self.sensor_on}
        ):
            targets = alexa_tts.make_announcement(
                self.hass,
                message=self.test_message,
                silent_in=[alexa_tts.PRIMARY_BEDROOM],
            )

            self.assertEqual(
                targets,
                expected_targets,
                f"Should not be announced if silenced "  # pylint: disable=W1309
                "in {alexa_tts.PRIMARY_BEDROOM} during quite hours.",
            )
            self._assert_hass_called_with(self.test_message, expected_targets)


class TestSecondaryBathroom(TestArea):
    """Secondary bathroom tests."""

    def test_announced(self):
        super()._test_announced(
            alexa_tts.SECONDARY_BATHROOM,
            alexa_tts.SECONDARY_BATHROOM_ECHO,
            {
                alexa_tts.SECONDARY_BATHROOM_LIGHT: "when the light is on",
                alexa_tts.SECONDARY_BATHROOM_LIGHT: "when there was a recent motion",
            },
        )

    def test_not_announced(self):
        super()._test_not_announced(
            alexa_tts.SECONDARY_BATHROOM, alexa_tts.SECONDARY_BATHROOM_ECHO
        )


if __name__ == "__main__":
    unittest.main()
