"""
Plays a TTS message on Amazon Echo devices using Alexa notification service.
A list of target devices is generated based on time, recent motion activity,
and a set of default and last resort targets.

"""

__author__ = "Ark (ark@cho.red)"

import sys
from queue import Queue
from threading import Thread

from appdaemon.plugins.hass import hassapi as hass


class AlexaTTS(hass.Hass):
  """Alexa TTS App Daemon class."""

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

  QUITE_TIME = "binary_sensor.quite_time"

  STATE_OFF = "off"
  STATE_ON = "on"

  ENV = {
      "NORMAL_TIME_DEFAULT_TARGETS": {},
      "NORMAL_TIME_LAST_RESORT_TARGETS": {
          CORRIDOR: CORRIDOR_ECHO
      },
      "QUITE_TIME_DEFAULT_TARGETS": {
          BEDROOM_1: BEDROOM_1_ECHO
      },
  }

  RULES = (
      {
          "conditions": (BATHROOM_1_LIGHT, BATHROOM_1_MOTION),
          "target": BATHROOM_1_ECHO,
          "unless": {
              "conditions": (BATHROOM_1_DOOR,),
              "target": BEDROOM_1_ECHO
          }
      },
      {
          "conditions": (BATHROOM_2_LIGHT, BATHROOM_2_MOTION),
          "target": BATHROOM_2_ECHO,
          "unless": {
              "conditions": (BATHROOM_2_DOOR,),
              "target": LIVING_ROOM_ECHO
          }
      },
      {
          "conditions": (BEDROOM_1_LIGHT, BEDROOM_1_MOTION),
          "target": BEDROOM_1_ECHO
      },
      {
          "conditions": (GARAGE_LIGHT, GARAGE_MOTION),
          "target": GARAGE_ECHO
      },
      {
          "conditions": (
              DINING_AREA_LIGHT,
              HALLWAY_MOTION,
              KITCHEN_LIGHT,
              KITCHEN_MOTION,
              LIVING_ROOM_LIGHT,
              LIVING_ROOM_MOTION,
              LIVING_ROOM_TV,
          ),
          "target": LIVING_ROOM_ECHO
      },
      {
          "conditions": (OFFICE_1_LIGHT, OFFICE_1_MOTION, OFFICE_1_TV),
          "target": OFFICE_1_ECHO,
          "unless": {
              "conditions": (DINING_AREA_LIGHT, KITCHEN_LIGHT, KITCHEN_TV,
                             LIVING_ROOM_LIGHT, LIVING_ROOM_TV),
              "target": LIVING_ROOM_ECHO
          }
      },
      {
          "conditions": (OFFICE_2_LIGHT, OFFICE_2_MOTION),
          "target": OFFICE_2_ECHO
      },
  )

  def initialize(self):
    """Initialize event listener."""

    # pylint: disable=attribute-defined-outside-init
    self.messages = Queue(maxsize=5)

    thread = Thread(target=self.worker)
    thread.daemon = True
    thread.start()

    self.listen_event(self.handle_event, "tts")

  # pylint: disable=unused-argument
  def handle_event(self, event, data, kwargs):
    """Put new message to the queue."""

    self.messages.put({
        "silent_in": data.get("silent_in"),
        "text": data.get("text"),
    })

  # pylint: disable=too-many-branches
  def tts(self, text=None, silent_in=None, env=None):
    """
      Check targets and generate text to speech API request.

      Parameters:
        hass: A HomeAssistant service from the global context.
        text: A text to play.
        silent_in: A list of areas to exclude.
        env: An environment settings for normal/quite time.

      Returns:
        list: A list of target devices the message to be played on.
      """

    def is_on(sensor):
      """
        Return True if sensor's state is "on" otherwise returns False.
      """

      return self.get_state(sensor) == self.STATE_ON

    if not text:
      raise ValueError("Message is required.")

    quite_hours = is_on(self.QUITE_TIME)

    targets = set()

    # Add targets based on the rule conditions.
    for rule in self.RULES:
      if any((is_on(c) for c in rule["conditions"])):
        targets.add(rule["target"])

    # Remove targets based on the unless condition.
    for rule in self.RULES:
      target = rule["target"]
      if (target not in targets or "unless" not in rule
          or rule["unless"]["target"] not in targets):
        continue

      conditions = rule["unless"]["conditions"]
      if not conditions:
        targets.remove(target)
      elif any((is_on(c) for c in conditions)):
        targets.remove(target)

    # Mute silenced targets.
    silenced_targets = {f"media_player.{area}_echo" for area in silent_in or ()}
    targets = targets.difference(silenced_targets)

    # Add default and last resort targets.
    if quite_hours:
      if "QUITE_TIME_DEFAULT_TARGETS" in env:
        targets.update(
            set(env["QUITE_TIME_DEFAULT_TARGETS"].values()).difference(
                silenced_targets))
    else:
      if "NORMAL_TIME_DEFAULT_TARGETS" in env:
        targets.update(
            set(env["NORMAL_TIME_DEFAULT_TARGETS"].values()).difference(
                silenced_targets))

      if not targets and "NORMAL_TIME_LAST_RESORT_TARGETS" in env:
        targets.update(
            set(env["NORMAL_TIME_LAST_RESORT_TARGETS"].values()).difference(
                silenced_targets))

    targets = list(targets)
    if targets:
      self.log(targets)
      self.call_service("notify/alexa_media",
                        target=targets,
                        message=text,
                        data={"type": "tts"})
    return targets

  def worker(self):
    """Process TTS messages from the queue."""

    while True:
      try:
        data = self.messages.get()
        self.tts(text=data["text"], silent_in=data["silent_in"], env=self.ENV)
      except Exception:  # pylint: disable=broad-except
        self.log(sys.exc_info())

      self.messages.task_done()
