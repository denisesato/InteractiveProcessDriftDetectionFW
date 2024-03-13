# InteractiveProcessDriftDetectionFW
This is a public repository for Interactive Process Drift Detection (IPDD) Framework, a tool for detecting process drifts in process models. 

# Installation from source-code repository
This installation process was tested on a Windows 10 machine with Python 3.12.2. 

After you cloned the git repository, go to the project directory and install the dependencies (using pip):

	pip install -r requirements.txt

# New release

We have updated IPDD to use the ADWIN detector implementation from River package (https://github.com/online-ml/river).

## Information about new version of pm4py
We have updated the pm4py from version 2.2.20.1 to version 2.7.11. After this update the pm4py inductive miner return more precise models, which affects the precision metric value used by IPDD for detecting the concept drifts. Because of this difference, when executing the updated version of IPDD will result on different detections for some scenarios when comparing to the reported results at my thesis: https://www.ppgia.pucpr.br/pt/arquivos/doutorado/teses/2022/Tese_Denise_Maria_Vecino_Sato.pdf. 

"Since the release of pm4py 2.3.0, the inductive miner has been refactored. In particular, a change of interest is the introduction of the "strict sequence cut" in place of the traditional "sequence cut". This type of sequence cut provides generally more precise models, but results in models that are different." - information provided by Alessandro Berti from pm4py team. 

# Running IPDD
## Running the web interface
You can start the IPDD web interface by running the file index.py.

The application will be accessible by any browser using the URL http://localhost:8050/.

2 datasets containing event logs with drifts are available for download at https://github.com/denisesato/SimulateLogsWithDrifts/tree/master/data/output/drift. 

Steps for analyzing drifts using IPDD:

1) Start the IPDD Framework. 
 
2) Check if the desired event log is listed. If not, you can drop or select an XES file, then IPDD will include it on the list.

3) Select the desired XES file from the list. IPDD shows a preview of the event log. 

4) Click on "Process Drift Analysis" to access the main page for drift analysis.

5) On the main page, the user must define:

	Approach - Fixed or Adaptive 
   
   	- Parameters for Fixed IPDD:
   	
	Window size - a numeric value indicating the size of the window (number of traces)
   
   	- Parameters for Adaptive IPDD:
   	
	Perspective - Time/Data or Control-flow
   
   	In case of Time/Data you can select the attribute for applying the adaptive drift detection.
   
   	In case of Control-flow you can select between the two approaches: Trace by Trace or windowing, and set the Window size (a numeric value indicating the size of the window - number of traces)

6) Click on "Analyze Process Drifts" to start the drift analysis. 

IPDD will inform the user when it finishes to mine the models and calculate the similarity metrics.

After analyzing the process drifts, the user can navigate between windows to check the process models and the similarity metrics, visualizing the drifts. The windows are named using the number of the window and the trace index of the initial trace of the window.

Windows marked as read indicates a process drift. 

Optionally the user can evaluate the detected drifts. This is possible when the event log is artificial and the position of the drifts is a priori known.

1) Select "Evaluate results"
2) Inform all the actual drifts, using the trace/event indexes, separated by a space.
3) Click on "Evaluate"

IPDD shows the F-score, FPR and Mean Delay metrics calculated using the informed actual drifts. 

## Running the command line interface

It is also possible to execute IPDD by the command line. In this case, IPDD saves the outputted information about the process drifts into the “data/output” folder. You have to create a virtual environment containing the dependencies of IPDD (numpy, requirements.txt, and scikit-multiflow-0.6.dev0.tar.gz)

To run IPDD via command line you can verify the parameter by running from the virtual environment: 
python ipdd_cli.py -h

You may also check the file run_manufaturing_synthetic_experiments_CLI.py, which performed several experiments using the CLI interface.

## Running the massive interface of IPDD 

If you want to perform the drift analysis using different parameters, e.g., analysing the same log with a range of window sizes, you can use the massive interface (ipdd_massive.py). 

You can check the file run_thesis_experiments_massive.py, which performed massive experiments on a dataset containing 68 event logs.
