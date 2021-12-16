from enum import Enum


class ReadLogAs(str, Enum):
    TRACE = 'Stream of Traces'
    EVENT = 'Event Stream'


class WindowUnityFixed(str, Enum):
    UNITY = 'Item'
    HOUR = 'Hours'
    DAY = 'Days'


class AttributeAdaptive(str, Enum):
    SOJOURN_TIME = 'Sojourn Time'
    WAITING_TIME = 'Waiting time'


class Approach(str, Enum):
    FIXED = 'Fixed'
    ADAPTIVE = 'Adaptive'
