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
    TRACE = 'Trace by trace'
    WINDOW = 'Windowing'


class Approach(str, Enum):
    FIXED = 'Fixed'
    ADAPTIVE = 'Adaptive'


def get_value_of_parameter(name):
    if name == ControlflowAdaptiveApproach.TRACE.name:
        return ControlflowAdaptiveApproach.TRACE.value
    elif name == ControlflowAdaptiveApproach.WINDOW.name:
        return ControlflowAdaptiveApproach.WINDOW.value
    elif name == Approach.ADAPTIVE.name:
        return Approach.ADAPTIVE.value
    elif name == Approach.FIXED.name:
        return Approach.FIXED.value
    elif name == AdaptivePerspective.CONTROL_FLOW.name:
        return AdaptivePerspective.CONTROL_FLOW.value
    elif name == AdaptivePerspective.TIME_DATA.name:
        return AdaptivePerspective.TIME_DATA.value
    elif name == AttributeAdaptive.SOJOURN_TIME.name:
        return AttributeAdaptive.SOJOURN_TIME.value
    elif name == AttributeAdaptive.WAITING_TIME.name:
        return AttributeAdaptive.WAITING_TIME.value
    elif name == AttributeAdaptive.OTHER.name:
        return AttributeAdaptive.OTHER.value
    else:
        return "Parameter not recognized"