from enum import IntEnum
from typing import List, Dict

###
# Encodings
###


class DirectionMoved(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

###
# JSON Schemas
###


class ButtonModel(object):
    def __init__(self, button_state: int):
        self.button_state = button_state


class SwitchModel(object):
    def __init__(self, switch_state: int):
        self.switch_state = switch_state


class DirectionModel(object):
    def __init__(self, directions_moved: List[int]):
        self.directions_moved = directions_moved


class NiosDataModel(object):
    def __init__(self, axes: List[int], buttons: int, switches: int):
        self.axes = axes
        self.buttons = buttons
        self.switches = switches
