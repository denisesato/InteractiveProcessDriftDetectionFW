# InteractiveProcessDriftDetectionFW
This is a public repository for Interactive Process Drift Detection (IPDD) Framework, a tool for detecting process drifts in process models. 

# Installation from source-code repository
This installation process was tested on a Windows 10 machine.

After you cloned the git repository, you can install the dependencies using the requirements.txt file (using pip):
pip install -r requirements.txt

# Docker installation
It is possible to install IPDD via docker using the Dockerfile. If you need any help please verify the file docker_help.txt. In this case you don't need to change requirements.txt file. 

# Running the web interface
You can start the IPDD web interface by running the file index.py.

The application will be accessible by any browser using the URL http://localhost:8050/.

72 event logs containing drifts are available for download at Business Process Drift dataset (https://data.4tu.nl/articles/dataset/Business_Process_Drift/12712436 - Reference http://eprints.qut.edu.au/83013/). 

Steps for analyzing drifts using IPDD:
1) Check if the event log is listed. If not, the user can drop an XES file, then IPDD will include it on the list.
2) Select an XES file from the list. IPDD shows a preview of the event log. 
3) Click on "Process Drift Analysis" to access the main page for drift analysis.
3) On the main page, the user must define:

a. Read as - the log can be read as: 
     - Stream of traces: log is read trace by trace, sorting the traces based on the timestamp of the first event
     - Event stream: log is read event by event, based on their timestamps

b. Window type - define how the windowing strategy will split the log 
     - Traces/events: number of traces or events (depending on the windowing strategy's choice)
     - Days: number of days 
     - Hours: number of hours
     
c. Window size - a numeric value indicating the size of the window

4) Click on "Analyze Process Drifts" to start the drift analysis. 

IPDD will inform the user when it finishes to mine the models and calculate the similarity metrics.

After analyzing the process drifts, the user can navigate between windows to check the process models and the similarity metrics, visualing the drifts. The windows are named using the number of the window and the trace index of the first trace considered inside the window.

Windows marked as read indicates a process drift. 

Optionally the user can evaluate the detected drifts. This is possible when the event log is artificial and the position of the drifts is a priori known.
1) Select "Evaluate results"
2) Inform all the actual drifts, using the trace/event indexes, separated by a space.
3) Click on "Evaluate"

IPDD shows the F-score metric calculated using the informed actual drifts. 

# Running the command line interface

It is also possible to execute IPDD by the command line. In this case, IPDD saves the process models for each window and the similarity metrics into the “data” folder. 
The process models are stored using the DOT format. IPDD saves the similarity metrics for the windows identified as drifts using the JSON format. 

To run IPDD via command line (“wz” indicates the window size and “l” refers to the event log):

python ipdd_cli.py -wz 250 -l "C:\logs\cb2.5k.xes" 

For IPDD also calculates the F-score, inform the real drifts in the “rd” parameter:

python ipdd_cli.py -wz 250 -l "C: \logs\cb2.5k.xes" -rd 250 500 750 1000 1250 1500 1750 2000 2250

Parameters:
-wt: Window type: t - stream of traces or e - event stream (default t)
-wu: Window unity: u - amount of traces or events, h - hours, or d – days (default u)
-wz: Window size: numeric value indicating the total of window unities for each window
-l: Event log: path and name of the event log using XES format
-rd: Real drifts: list of trace indexes from actual drifts (separated by a space), used for evaluation

