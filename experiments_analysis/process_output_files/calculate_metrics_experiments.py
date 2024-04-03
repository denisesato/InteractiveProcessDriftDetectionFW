from evaluation_metrics import calculate_metrics_dataset
from execute_experiments import Dataset1Configuration, Dataset2Configuration

# defined metrics
metrics = [
    'f_score',
    'mean_delay',
    'mean_detection_delay',
    'FPR'
]


def calculate_metrics_for_dataset(dataset_config, dataset_name):
    ipdd_quality_trace_path = f'data/experiments_results/IPDD_controlflow_adaptive/detection_on_quality_metrics_trace_by_trace' \
                              f'//{dataset_name}'
    ipdd_quality_trace_filename = 'experiments_quality_metrics_trace_by_trace.xlsx'

    calculate_metrics_dataset(ipdd_quality_trace_path, ipdd_quality_trace_filename, metrics, dataset_config,
                              save_input_for_calculation=True)

    ipdd_quality_windowing_path = f'data/experiments_results/IPDD_controlflow_adaptive/detection_on_quality_metrics_fixed_window' \
                                  f'//{dataset_name}'
    ipdd_quality_windowing_filename = 'experiments_quality_metrics_fixed_window.xlsx'
    calculate_metrics_dataset(ipdd_quality_windowing_path, ipdd_quality_windowing_filename, metrics, dataset_config,
                              save_input_for_calculation=True)

    prodrift_filepath = f'data/experiments_results/Apromore/experimento2/{dataset_name}'
    prodrift_filename = 'results_prodrift.xlsx'
    calculate_metrics_dataset(prodrift_filepath, prodrift_filename, metrics, dataset_config,
                              save_input_for_calculation=True)

    vdd_filepath = f'data/experiments_results/VDD/experimento2/{dataset_name}/output_console'
    vdd_filename = 'results_VDD.xlsx'
    calculate_metrics_dataset(vdd_filepath, vdd_filename, metrics, dataset_config,
                               save_input_for_calculation=True)


if __name__ == '__main__':
    dataset_name = "dataset1"
    dataset_config = Dataset1Configuration()
    calculate_metrics_for_dataset(dataset_config, dataset_name)
    dataset_name = "dataset2"
    dataset_config = Dataset2Configuration()
    calculate_metrics_for_dataset(dataset_config, dataset_name)
