from json_tricks import dumps


class MetricInfo:
    def __init__(self, window, metric_name):
        self.diff_added = set()
        self.diff_removed = set()
        self.value = 0
        self.window = window
        self.metric_name = metric_name

    def serialize(self):
        result = dumps(self)
        return result

    def set_value(self, value):
        self.value = value

    def set_diff_added(self, diff):
        self.diff_added = diff

    def set_diff_removed(self, diff):
        self.diff_removed = diff

    def serialize(self):
        result = dumps(self)
        return result