from json_tricks import dumps


class MetricInfo:
    def __init__(self, window, metric_name):
        self.diff = set()
        self.value = 0
        self.window = window
        self.metric_name = metric_name

    def serialize(self):
        result = dumps(self)
        return result

    def set_value(self, value):
        self.value = value

    def set_diff(self, diff):
        self.diff = diff

    def serialize(self):
        result = dumps(self)
        return result