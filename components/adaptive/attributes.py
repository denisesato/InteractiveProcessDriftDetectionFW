from components.parameters import AttributeAdaptive


class SelectAttribute:
    @staticmethod
    def get_selected_attribute_class(attribute_name):
        # define todas as classes de atributo disponíveis
        # porém só será retornada aquela escolhida pelo usuário
        classes = {
            AttributeAdaptive.SOJOURN_ACTIVITY_TIME.name: SojournActivityTime(attribute_name),
        }
        return classes[attribute_name]

class SojournActivityTime:
    def __init__(self, name):
        self.name = name

    def get_value(self, event):
        # get the duration of the event
        # the input must be an interval log
        start_time = event['start_timestamp'].timestamp()
        complete_time = event['time:timestamp'].timestamp()
        duration = complete_time - start_time
        return duration