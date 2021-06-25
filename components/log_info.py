class LogInfo:
    def __init__(self, complete_filename, filename):
        self.complete_filename = complete_filename
        self.filename = filename
        self.log = None
        self.first_traces = None
        self.median_case_duration = None
        self.median_case_duration_in_hours = None
        self.total_of_cases = None