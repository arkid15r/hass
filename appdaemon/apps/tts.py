"""
Plays a TTS message on Amazon Echo devices using Alexa notification service.
A list of target devices is generated based on time, recent motion activity,
and a set of default and last resort targets.

"""

__author__ = "Ark (ark@cho.red)"

import sys
import time
from queue import Queue
from threading import Thread

# pylint: disable=import-error
from appdaemon.plugins.hass import hassapi as hass

# pylint: disable=attribute-defined-outside-init
# pylint: disable=too-many-instance-attributes


class Alexa(hass.Hass):
  """Alexa TTS App Daemon class."""

  STATE_OFF = "off"
  STATE_ON = "on"

  TTS_DURATION_DEFAULT_SECONDS = 5

  def initialize(self):
    """Initialize event listener."""

    self.env = self.args["env"]
    self.rules = self.args["rules"]
    self.quite_time = self.args["quite_time"]

    self.messages = Queue(maxsize=5)

    self.play_always_normal_time = []
    self.play_always_quite_time = []
    self.play_default_normal_time = []
    self.play_default_quite_time = []

    thread = Thread(target=self.worker)
    thread.daemon = True
    thread.start()

    self.listen_event(self.handle_event, "tts")

  # pylint: disable=unused-argument
  def handle_event(self, event, data, kwargs):
    """Put new message to the queue."""

    self.messages.put({
        "areas_off": data.get("areas_off"),
        "areas_on": data.get("areas_on"),
        "text": data.get("text"),
    })

  @staticmethod
  def get_target(area):
    """Return media player target ID for an area."""

    return f"media_player.{area}_echo"

  def set_environment(self):
    """Add play always and play default area targets."""

    try:
      self.play_always_normal_time = [
          self.get_target(area)
          for area in self.env["play_always"]["normal_time"]
      ]
    except KeyError:
      pass

    try:
      self.play_always_quite_time = [
          self.get_target(area)
          for area in self.env["play_always"]["quite_time"]
      ]
    except KeyError:
      pass

    try:
      self.play_default_normal_time = [
          self.get_target(area)
          for area in self.env["play_default"]["normal_time"]
      ]
    except KeyError:
      pass

    try:
      self.play_default_quite_time = [
          self.get_target(area)
          for area in self.env["play_default"]["quite_time"]
      ]
    except KeyError:
      pass

  # pylint: disable=too-many-branches
  def tts(self, text=None, areas_off=None, areas_on=None):
    """
      Check targets and generate text to speech API request.

      Parameters:
        text: A text to play.
        areas_off: A list of explicitely excluded areas.
        areas_on: A list of explicitely included areas.

      Returns:
        list: A list of target devices the message to be played on.
      """

    def is_on(sensor):
      """Return True if sensor's state is "on" otherwise returns False."""
      return self.get_state(sensor) == self.STATE_ON

    # tts()
    if text is None:
      raise ValueError("Text is required.")

    if not text:
      raise ValueError("Text mustn't be empty.")

    if areas_off and areas_off == "*" and areas_on and areas_on == "*":
      raise ValueError(
          "You can't use wildcard targets for both areas_off and areas_on at "
          "the same time.")

    targets_all = [self.rules[rule]["target"] for rule in self.rules]

    self.set_environment()
    for targets in (self.play_always_normal_time, self.play_always_quite_time,
                    self.play_default_normal_time,
                    self.play_default_quite_time):
      if targets:
        targets_all.extend(targets)

    if areas_off == "*":
      targets_off = set(targets_all)
    else:
      targets_off = {self.get_target(area) for area in areas_off or ()}

    if areas_on == "*":
      targets_on = set(targets_all)
    else:
      targets_on = {self.get_target(area) for area in areas_on or ()}

    targets = set()
    # Add targets based on the rule conditions.
    for area in self.rules:
      rule = self.rules[area]

      if any((is_on(c) for c in rule["conditions"])):
        targets.add(rule["target"])

    # Remove targets based on the if_not condition.
    for area in self.rules:
      rule = self.rules[area]
      target = rule["target"]

      if (target not in targets or "if_not" not in rule
          or rule["if_not"]["target"] not in targets):
        continue

      conditions = rule["if_not"].get("conditions", ())
      if not conditions or any((is_on(c) for c in conditions)):
        targets.remove(target)

    # Update targets based on areas_off/areas_on values.
    targets.update(targets_on)
    targets = targets.difference(targets_off)

    targets_play_always = None
    targets_play_default = None
    if is_on(self.quite_time):
      targets_play_always = self.play_always_quite_time
      targets_play_default = self.play_default_quite_time
    else:
      targets_play_always = self.play_always_normal_time
      targets_play_default = self.play_default_normal_time

    if targets_play_always:
      targets.update(set(targets_play_always).difference(targets_off))

    if not targets and targets_play_default:
      targets.update(set(targets_play_default).difference(targets_off))

    targets = sorted(targets)
    if targets:
      self.log(f"Playing '{text}' on {targets}")
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
        self.tts(text=data["text"],
                 areas_off=data["areas_off"],
                 areas_on=data["areas_on"])
        time.sleep(data.get("duration", self.TTS_DURATION_DEFAULT_SECONDS))
      except Exception:  # pylint: disable=broad-except
        self.log(sys.exc_info())

      self.messages.task_done()
