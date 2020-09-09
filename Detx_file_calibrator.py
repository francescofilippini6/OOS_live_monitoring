import numpy as np
import io
import os
import sys
import matplotlib
from tabulate import tabulate
import pandas as pd
import matplotlib.pyplot as plt



def calibration_file_reader():
    delays = pd.read_csv('calibration.csv')
    #print(delays)
    return delays

def detx_file_reader():
    delay=calibration_file_reader()
    detx = open('D_BCI_NO_cali.detx','r')
    detout=open('D_BCI_Calibrated.detx','w')
    #skipping dom1 and the first 4 lines of header
    for header in range(0,36):
        he=detx.readline()
        detout.write(he)

    for body in range (2,19):
        #first line to skip with dom id pmt number ...
        detout.write(detx.readline())
        #read the 31 lines of the pmts
        for pmt in range(0,31):
            #dom 6 by now not working => time offset still at 0
            if body == 6:
                a6=detx.readline()
                detout.write(a6)
                continue
            
            a=detx.readline()
            b=a.split()
            if pmt < 12:
                b[-1]=list(delay.loc[delay.DOMnumber==float(body), 'deltaT'])[0]
            else:
                b[-1]=list(delay.loc[delay.DOMnumber==float(body), 'deltaT'])[1]
                
            detout.write(' '+' '.join([str(elem) for elem in b])+'\n')
            
            
detx_file_reader()



