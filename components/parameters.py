from enum import Enum


class ReadLogAs(str, Enum):
    TRACE = 'Stream of Traces'
    EVENT = 'Event Stream'


class WindowUnityFixed(str, Enum):
    UNITY = 'Item'
    HOUR = 'Hours'
    DAY = 'Days'


class AdaptivePerspective(str, Enum):
    TIME_DATA = 'Time/Data'
    CONTROL_FLOW = 'Control-flow'


class AttributeAdaptive(str, Enum):
    SOJOURN_TIME = 'Sojourn Time'
    WAITING_TIME = 'Waiting time'
    OTHER = 'Other attribute'


class ControlflowAdaptiveApproach(str, Enum):
    CONTROL_FLOW_TRACE = 'Trace by trace'
    CONTROL_FLOW_WINDOW = 'Windowing'


class Approach(str, Enum):
    FIXED = 'Fixed'
    ADAPTIVE = 'Adaptive'
