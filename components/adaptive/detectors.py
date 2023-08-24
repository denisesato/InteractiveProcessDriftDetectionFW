from enum import Enum
from skmultiflow.drift_detection.adwin import ADWIN
from river import drift


class ConceptDriftDetector(str, Enum):
    ADWIN = 'adwin'
    HDDM_A = 'hddm_a'


class SelectDetector:
    @staticmethod
    def get_selected_detector(detector_name):
        # define the class for each available detector
        classes = {
            ConceptDriftDetector.ADWIN.name: AdwinDetector(),
            ConceptDriftDetector.HDDM_A.name: HddmADetector(),
        }
        return classes[detector_name]

    @staticmethod
    def get_detector_instance(detector_name, parameters):
        # define the class for each available detector
        classes = {
            ConceptDriftDetector.ADWIN.name: AdwinDetector(parameters),
            ConceptDriftDetector.HDDM_A.name: HddmADetector(parameters),
        }
        return classes[detector_name]


class DetectorWrapper:
    def get_name(self):
        return self.name

    def get_definition(self):
        return self.definition

    def get_parameters_string(self):
        detector_parameters = ''
        for key in self.parameters:
            detector_parameters += f'_{key}{self.parameters[key]}'
        return detector_parameters

    def set_parameter(self, key, value):
        if key in self.default_parameters.keys():
            self.parameters[key] = value
        else:
            print(f'Parameter {key} does not exist for detector {self.name}')


class AdwinDetector(DetectorWrapper):
    def __init__(self, parameters=None):
        self.detector = None
        self.name = ConceptDriftDetector.ADWIN.value
        self.definition = ConceptDriftDetector.ADWIN.name
        self.default_parameters = {'delta': 0.002}
        if parameters:
            self.parameters = parameters
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


class HddmADetector(DetectorWrapper):
    def __init__(self, parameters=None):
        self.detector = None
        self.name = ConceptDriftDetector.HDDM_A.value
        self.definition = ConceptDriftDetector.HDDM_A.name
        self.default_parameters = {'drift_confidence': 0.002,
                                   'warning_confidence': 0.005,
                                   'two_sided_test': False}
        if parameters:
            self.parameters = parameters
        else:
            self.parameters = self.default_parameters

    def instantiate_detector(self):
        self.detector = drift.binary.HDDM_A(drift_confidence=self.parameters['drift_confidence'],
                                            warning_confidence=self.parameters['warning_confidence'],
                                            two_sided_test=self.parameters['two_sided_test'])

    def update_val(self, value):
        self.detector.update(value)

    def detected_change(self):
        return self.detector.drift_detected

    def reset(self):
        self.detector = drift.binary.HDDM_A(drift_confidence=self.parameters['drift_confidence'],
                                            warning_confidence=self.parameters['warning_confidence'],
                                            two_sided_test=self.parameters['two_sided_test'])
