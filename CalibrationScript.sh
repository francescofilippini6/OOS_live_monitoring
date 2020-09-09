#!/bin/bash

#removing the previous calbration.csv and D_BCI_Calibrated.detx file to not append it]
#remember to put in run all the BCI and to received data, otherwise ...................

rm calibration.csv
rm D_BCI_Calibrated.detx

python Delay_extractor_detfile_update.py 


python Detx_file_calibrator.py
