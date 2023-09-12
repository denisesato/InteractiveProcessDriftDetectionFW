from enum import Enum
from skmultiflow.drift_detection.adwin import ADWIN
from river import drift


class ConceptDriftDetector(str, Enum):
    ADWIN = 'adwin'
    HDDM_W = 'hddm_w'


class SelectDetector:
    @staticmethod
    def get_selected_detector(detector_name):
        # define the class for each available detector
        classes = {
            ConceptDriftDetector.ADWIN.name: AdwinDetector(),
            ConceptDriftDetector.HDDM_W.name: HddmWDetector()
        }
        return classes[detector_name]

    @staticmethod
    def get_detector_instance(detector_name, parameters=None, factor=None):
        # define the class for each available detector
        detector_class = SelectDetector.get_selected_detector(detector_name)
        detector_class.add_parameters(parameters)
        if factor:
            detector_class.set_factor(factor)
        return detector_class


class DetectorWrapper:
    def __init__(self):
        self.parameters = {}
        self.detector = None
        self.factor = 1

    def get_name(self):
        return self.name

    def get_definition(self):
        return self.definition

    def get_parameters_string(self):
        detector_parameters = ''
        for key in self.parameters:
            detector_parameters += f'_{key}{self.parameters[key]}'
        return detector_parameters

    def add_parameters(self, parameters=None):
        if parameters:
            for key in parameters:
                self.set_parameter(key, parameters[key])
        else:
            self.parameters = self.default_parameters

    def set_parameter(self, key, value):
        if key in self.default_parameters.keys():
            self.parameters[key] = value
        else:
            print(f'Parameter {key} does not exist for detector {self.name}')

    def set_factor(self, factor):
        self.factor = factor


class AdwinDetector(DetectorWrapper):
    def __init__(self, parameters=None, factor=100):
        super().__init__()
        super().set_factor(factor)
        self.name = ConceptDriftDetector.ADWIN.value
        self.definition = ConceptDriftDetector.ADWIN.name
        self.default_parameters = {'delta': 0.002}
        if parameters:
            self.add_parameters(parameters)
        else:
            self.parameters = self.default_parameters

    def instantiate_detector(self):
        self.detector = ADWIN(delta=self.parameters['delta'])

    def update_val(self, value):
        self.detector.add_element(value)

    def detected_change(self):
        return self.detector.detected_change()

    def reset(self):
        self.detector.reset()


class HddmWDetector(DetectorWrapper):
    def __init__(self, parameters=None, factor=10):
        super().__init__()
        super().set_factor(factor)
        self.name = ConceptDriftDetector.HDDM_W.value
        self.definition = ConceptDriftDetector.HDDM_W.name
        self.default_parameters = {'drift_confidence': 0.001,
                                   'warning_confidence': 0.005,
                                   'lambda_val': 0.05,
                                   'two_sided_test': False}
        if parameters:
            self.add_parameters(parameters)
        else:
            self.parameters = self.default_parameters

    def instantiate_detector(self):
        self.detector = drift.binary.HDDM_W(drift_confidence=self.parameters['drift_confidence'],
                                            warning_confidence=self.parameters['warning_confidence'],
                                            lambda_val=self.parameters['lambda_val'],
                                            two_sided_test=self.parameters['two_sided_test'])

    def update_val(self, value):
        self.detector.update(value)

    def detected_change(self):
        return self.detector.drift_detected

    def reset(self):
        self.instantiate_detector()
