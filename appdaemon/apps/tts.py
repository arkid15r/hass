"""
Plays a TTS message on Amazon Echo devices using Alexa notification service.
A list of target devices is generated based on time, recent motion activity,
and a set of default and last resort targets.

"""

__author__ = 'Ark (ark@cho.red)'

# pylint: disable=attribute-defined-outside-init
# pylint: disable=import-error
# pylint: disable=too-many-instance-attributes

import sys
import time
from queue import Queue
from threading import Thread

from appdaemon.plugins.hass import hassapi as hass


class AmazonEcho(hass.Hass):
  """Amazon Echo TTS App Daemon class."""

  EVENT_NAME = 'tts'
  STATE_OFF = 'off'
  STATE_ON = 'on'
  TTS_DURATION_DEFAULT_SECONDS = 7

  def initialize(self):
    """Initialize event listener."""

    self.env = self.args['env']
    self.rules = self.args['rules']
    self.quite_time = self.args['quite_time']

    self.messages = Queue(maxsize=5)

    self.play_always_normal_time = []
    self.play_always_quite_time = []
    self.play_default_normal_time = []
    self.play_default_quite_time = []

    thread = Thread(target=self.worker)
    thread.daemon = True
    thread.start()

    self.listen_event(self.handle_event, self.EVENT_NAME)

  # pylint: disable=unused-argument
  def handle_event(self, event, data, kwargs):
    """Put new message to the queue."""

    self.messages.put({
        'areas_off': data.get('areas_off'),
        'areas_on': data.get('areas_on'),
        'duration': data.get('duration', self.TTS_DURATION_DEFAULT_SECONDS),
        'text': data.get('text'),
    })

  @staticmethod
  def get_target(area):
    """Return media player target ID for an area."""

    return f'media_player.{area}_echo'

  def set_environment(self):
    """Add play always and play default area targets."""

    try:
      self.play_always_normal_time = [
          self.get_target(area)
          for area in self.env['play_always']['normal_time']
      ]
    except KeyError:
      pass

    try:
      self.play_always_quite_time = [
          self.get_target(area)
          for area in self.env['play_always']['quite_time']
      ]
    except KeyError:
      pass

    try:
      self.play_default_normal_time = [
          self.get_target(area)
          for area in self.env['play_default']['normal_time']
      ]
    except KeyError:
      pass

    try:
      self.play_default_quite_time = [
          self.get_target(area)
          for area in self.env['play_default']['quite_time']
      ]
    except KeyError:
      pass

  # pylint: disable=too-many-branches
  def tts(self, text=None, areas_off=None, areas_on=None):
    """
      Check targets and generate text to speech API request.

      Parameters:
        text: A text to play.
        areas_off: A list of explicitly excluded areas.
        areas_on: A list of explicitly included areas.

      Returns:
        list: A list of target devices the message to be played on.
      """

    def in_dnd_mode(media_player):
      """
      Return True if media player device is in the "Do Not Disturb" mode.
      Return False otherwise.
      """
      return is_on(f'switch.{media_player.split(".")[1]}_do_not_disturb_switch')

    def is_on(sensor):
      """Return True if sensor's state is 'on' otherwise returns False."""
      return self.get_state(sensor) == self.STATE_ON

    # tts()
    if text is None:
      raise ValueError('Text is required.')

    if not text:
      raise ValueError("Text mustn't be empty.")

    if areas_off and areas_off == '*' and areas_on and areas_on == '*':
      raise ValueError(
          "You can't use wildcard targets for both areas_off and areas_on at "
          "the same time.")

    targets_all = [self.rules[rule]['target'] for rule in self.rules]

    self.set_environment()
    for targets in (self.play_always_normal_time, self.play_always_quite_time,
                    self.play_default_normal_time,
                    self.play_default_quite_time):
      if targets:
        targets_all.extend(targets)

    if areas_off == '*':
      targets_off = set(targets_all)
    else:
      targets_off = {self.get_target(area) for area in areas_off or ()}

    if areas_on == '*':
      targets_on = set(targets_all)
    else:
      targets_on = {self.get_target(area) for area in areas_on or ()}

    targets = set()

    # Normal time targets.
    if not is_on(self.quite_time):
      # Add targets based on the rule conditions.
      for area in self.rules:
        rule = self.rules[area]

        if any((is_on(c) for c in rule['conditions'])):
          targets.add(rule['target'])

      # Remove targets based on the if_not conditions.
      for area in self.rules:
        rule = self.rules[area]
        rule_target = rule['target']

        if rule_target not in targets or 'if_not' not in rule:
          continue

        conditions = rule['if_not'].get('conditions', ())
        target = rule['if_not'].get('target')

        if target and target not in targets:
          continue

        if not conditions or any((is_on(c) for c in conditions)):
          targets.remove(rule_target)

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

    targets = sorted((target for target in targets if not in_dnd_mode(target)))
    if targets:
      self.call_service('notify/alexa_media',
                        data={'type': 'tts'},
                        message=text,
                        target=targets)
    return targets

  def worker(self):
    """Process TTS messages from the queue."""

    while True:
      try:
        data = self.messages.get()

        areas_off = data['areas_off']
        areas_on = data['areas_on']
        duration = data['duration']
        text = data['text']

        targets = self.tts(
            areas_off=areas_off,
            areas_on=areas_on,
            text=text,
        )
        self.log(f"{text} on {', '.join(targets)} ({duration}s)")
        time.sleep(duration)
      except Exception:  # pylint: disable=broad-except
        self.log(sys.exc_info())

      self.messages.task_done()
