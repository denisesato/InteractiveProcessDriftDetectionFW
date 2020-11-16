
class Precision:
    def __init__(self, tp, fp, fn):
        self.tp = tp
        self.fp = fp
        self.fn = fn

    def calculate(self):
        precision = 0
        if self.tp + self.fp > 0:
            precision = self.tp / (self.tp + self.fp)
        return precision


class Recall:
    def __init__(self, tp, fp, fn):
        self.tp = tp
        self.fp = fp
        self.fn = fn

    def calculate(self):
        recall = 0
        if self.tp + self.fn > 0:
            precision = self.tp / (self.tp + self.fn)
        return recall


class FScore:
    def __init__(self, precision, recall):
        self.precision = precision
        self.recall = recall

    def calculate(self):
        fscore = 0
        if self.precision + self.recall > 0:
            fscore = (2 * self.precision * self.recall) / (self.precision + self.recall)
        return fscore