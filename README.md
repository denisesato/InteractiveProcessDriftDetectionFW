# InteractiveProcessDriftDetectionFW
This is a public repository for Interactive Process Drift Detection (IPDD) Framework, a tool for detecting process drifts in process models. 

# Installation from source-code repository
This installation process was tested on a Windows 10 machine.

After you cloned the git repository, you can install the dependencies using the requirements.txt file (using pip):
pip install -r requirements.txt

Pygraphviz library do not install using pip in windows machines. Because of this the line for pygraphviz (in requirements.txt) is commented and there is a file named pygraphviz_windows.txt to help you with the installation.

# Docker installation
It is possible to install IPP via docker using the Dockerfile. If you need any help there is also a file named docker_help.txt

# Running the web interface
You can start the IPDD web interface by running the file index.py.

The application will be accessible by any browser using the URL http://localhost:8050/.
72 event logs containing drifts are available for download at Business Process Drift dataset (https://data.4tu.nl/articles/dataset/Business_Process_Drift/12712436 - Reference http://eprints.qut.edu.au/83013/). 

Steps for analyzing drifts using IPDD:
1) Check if the event log is listed. If not, the user can drop an XES file, then IPDD will include it on the list.
2) Select an XES file from the list. IPDD shows a preview of the event log. 
3) Click on "Analyze process drift" to access the main page for drift analysis.
3) On the main page, the user must define:
  a. Windowing strategy: 
     - Stream of traces: log is read trace by trace, sorting the traces based on the timestamp of the first event
     - Event stream: log is read event by event, based on their timestamps
  b. Window type: define how the windowing strategy will split the log 
     - Unity: number of traces or events (depending on the windowing strategy's choice)
     - Days: number of days
     - Hours: number of hours
  c. Window size: a numeric value indicating the size of the window
  d. Option for visualizing the windows on the interface: this parameter changes the windows' visualization after IPDD mines the process. For each window, IPDD shows the number of the window and the start trace considered. The user can select the trace index or trace name for this visualization. 
4) Click on "Mine Models" to start the drift analysis. IPDD will inform the user when finished to mine the models and calculate the similarity metrics.

IPDD shows the models for each window and marks windows with drifts in red. The user can then navigate between the models generated for each window, identifying the drifts.

Optionally the user can evaluate the detected drifts:
1) Select "Evaluate results"
2) Inform all the actual drifts, using the trace/event indexes, separated by a space.
3) Click on "Evaluate"

IPDD shows the F-score metric calculated using the informed actual drifts. 
