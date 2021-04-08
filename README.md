# InteractiveProcessDriftDetectionFW
Public repository for Interactive Process Drift Detection (IPDD) Framework, a tool for detecting process drifts in process models. 

# Running the web interface
After you cloned the git repository 

Then you can start the IPDD web interface by running file index.py.

The application will be acessible by be browser using the url http://localhost:8050/.
Some event logs from Business Process Drift dataset (https://data.4tu.nl/articles/dataset/Business_Process_Drift/12712436 - Reference http://eprints.qut.edu.au/83013/) are available, but the user can upload any XES file. 

Steps for analyzing drifts using IPDD:
1) Check if the event log is listed. If not the user can drop a XES file, then IPDD will include it on the list.
2) Select a XES file from the list. IPDD shows a preview of the event log. 
3) Click on "Analyze process drift" to access the main page for drift analysis.
3) On the main page the user must define:
  a. Windowing strategy: 
     - Stream of traces: log is read trace by trace, sorting the traces based on the timestamp of the first event
     - Event stream: log is read event by event, based on their timestamps
  b. Window type: define how the windowing strategy will split the log 
     - Unity: number of traces or events (depending on the windowing strategy's choice)
     - Days: number of days
     - Hours: number of hours
  c. Window size: numeric value indicating the size of the window
  d. Visualizing the beginning of windows: this parameter changes the visualization of the windows, after the process are mined by IPDD. For each window, IPDD shows the start trace by showing the trace index or trace name
4) Click on "Mine Models" to start the drift analysis. IPDD will inform the user when finished to mine the models and calculate the similarity metrics.

IPDD shows the models for each window and marks windows with drifts in red. The user can then navigate between the models generated for each window, identifying the drifts.

Optionally the user can evaluate the detected drifts:
1) Select "Evaluate results"
2) Inform all the actual drifts, using the trace/event indexes, separated by a space.
3) Click on "Evaluate"

IPDD shows the F-score metric based on the informed drifts. 


# Running IPDD from command line
