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


class Alexa(hass.Hass):
  """Alexa TTS App Daemon class."""

  STATE_OFF = "off"
  STATE_ON = "on"

  TTS_DURATION_DEFAULT_SECONDS = 5

  def initialize(self):
    """Initialize event listener."""

    # pylint: disable=attribute-defined-outside-init
    self.messages = Queue(maxsize=5)

    self.env = self.args["env"]
    self.rules = self.args["rules"]
    self.quite_time = self.args["quite_time"]

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
  def tts(self, text=None, silent_in=None):
    """
      Check targets and generate text to speech API request.

      Parameters:
        text: A text to play.
        silent_in: A list of areas to exclude.

      Returns:
        list: A list of target devices the message to be played on.
      """

    def is_on(sensor):
      """
        Return True if sensor's state is "on" otherwise returns False.
      """

      return self.get_state(sensor) == self.STATE_ON

    if not text:
      raise ValueError("Text is required.")

    quite_time = is_on(self.quite_time)

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

    # Mute silenced targets.
    silenced_targets = {f"media_player.{area}_echo" for area in silent_in or ()}
    targets = targets.difference(silenced_targets)

    # Add always and default play area targets.
    always_play_targets = None
    default_play_targets = None
    if quite_time:
      if "quite_time" in self.env.get("play_always", ()):
        always_play_targets = [
            f"media_player.{area}_echo"
            for area in self.env["play_always"].get("quite_time", ())
        ]

      if "quite_time" in self.env.get("play_default", ()):
        default_play_targets = [
            f"media_player.{area}_echo"
            for area in self.env["play_default"].get("quite_time", ())
        ]

    else:
      if "normal_time" in self.env.get("play_always", ()):
        always_play_targets = [
            f"media_player.{area}_echo"
            for area in self.env["play_always"].get("normal_time", ())
        ]

      if "normal_time" in self.env.get("play_default", ()):
        default_play_targets = [
            f"media_player.{area}_echo"
            for area in self.env["play_default"].get("normal_time", ())
        ]

    if always_play_targets is not None:
      targets.update(set(always_play_targets).difference(silenced_targets))

    if not targets and default_play_targets is not None:
      targets.update(set(default_play_targets).difference(silenced_targets))

    targets = list(targets)
    if targets:
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
        self.tts(text=data["text"], silent_in=data["silent_in"])
        time.sleep(self.TTS_DURATION_DEFAULT_SECONDS)
      except Exception:  # pylint: disable=broad-except
        self.log(sys.exc_info())

      self.messages.task_done()
