#!/bin/bash
export DETECTOR_ID=48
#D_BCI0004
# The ligier to get events (IO_EVT), timeslices (e.g. IO_TSSN) and
# summary slices (IO_SUM)
export DAQ_LIGIER_IP=192.168.0.21
export DAQ_LIGIER_PORT=5553
export TAGS_TO_MIRROR="IO_EVT, IO_SUM, IO_TSSN, MSG, IO_MONIT"

# The logger ligier (MSG)
export LOG_LIGIER_IP=192.168.0.19
export LOG_LIGIER_PORT=5553

# The command to start a ligier on the monitoring machine
export LIGIER_CMD="singularity exec /home/km3net/KM3NeT_Software/Jpp/images/Jpp_v13.0.0-alpha.6.sif JLigier"
export MONITORING_LIGIER_PORT=55530

export DETECTOR_MANAGER_IP=192.168.0.19

# The port for the KM3Web monitoring dashboard
export WEBSERVER_PORT=8081
# The port for the log viewer webserver
export LOGGING_PORT=8082

# The detector configuration to be used in the online reconstruction
export DETX="KM3NeT_00000048_30072020.detx"
# Where to save the time residuals
export ROYFIT_TIMERES="data/time_residuals.csv"
