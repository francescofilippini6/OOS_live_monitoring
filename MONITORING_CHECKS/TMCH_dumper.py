import numpy as np
import io
import os
import sys
import matplotlib
matplotlib.use('Agg')
import km3pipe as kp
import km3modules as km
from km3pipe.io.daq import TMCHData
from km3pipe import Module
from tabulate import tabulate
#from km3pipe.core import Pump
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import datetime

class OOSAnalyzer(Module):
    def configure(self):
        self.orderedDOM = [806451575,808981684,808447031,808985194,808971330,800000000,806451239,808952022,808967370,808489098,808976266,809537142,808984748,808982228,808980464,808976292,809544159,808996919]
        self.decimal = list(range(1, 19)) 
        self.Dom_id_name = {str(self.orderedDOM[i]) : self.decimal[i] for i in range(len(self.orderedDOM))}
        self.doms=[]
        self.times=[]
        #self.delays=[]
        self.numberofactivedom=0
        self.testdf=pd.DataFrame(columns=['DOM','time(s)','timeslice(s)','RunNumber','yaw','pitch','roll','aX','aY','aZ','gX','gY','gZ','hX','hY','hZ','Temp','Humid'])        
    
    def process(self,blob):
        #TMCH only for monitoring channel
        tmch_data = kp.io.daq.TMCHData(io.BytesIO(blob['CHData']))
        #print(tmch_data)
        #UTC_datetime = datetime.datetime.utcnow()
        #UTC_datetime_timestamp = float(UTC_datetime.strftime("%s"))
        #local_datetime_converted = datetime.datetime.fromtimestamp(UTC_datetime_timestamp) 
        timestamp_converted = datetime.datetime.fromtimestamp(tmch_data.utc_seconds) 
        #print('local time: ',local_datetime_converted)
        timestamp=tmch_data.utc_seconds+tmch_data.nanoseconds*10**-9
        #print(timestamp)
        #print('\nTimestamp = ',timestamp)
        #print('\nTimestamp in seconds = ',timestamp_converted)
        #print('DOM:',self.Dom_id_name[str(tmch_data.dom_id)])
        #print('Validity: ',tmch_data.flags)
        #print('Compass data: ',tmch_data.H)
        if tmch_data.nanoseconds*10**-9 == 0.5:
            self.testdf.loc[len(self.testdf)+1] = [self.Dom_id_name[str(tmch_data.dom_id)],timestamp_converted,timestamp,tmch_data.run,tmch_data.yaw,tmch_data.pitch,tmch_data.roll,tmch_data.A[0],tmch_data.A[1],tmch_data.A[2],tmch_data.G[0],tmch_data.G[1],tmch_data.G[2],tmch_data.H[0],tmch_data.H[1],tmch_data.H[2],tmch_data.temp,tmch_data.humidity]
            print("ciccio")
            #sys.exit()
        
        
    def finish(self):
        #print(self.testdf.sort_values(['DOM','timeslice(s)']))
        self.testdf.sort_values(['DOM','timeslice(s)']).to_csv('12-min-TMCH_Data_parsed',index=0)
        print("-------BYE BYE!! (As catom (dialatt regian)-------)")
        
        
    
def main():
    pipe=kp.Pipeline()
    pipe.attach(kp.io.ch.CHPump , host='192.168.0.21', port=5553,tags='IO_MONIT',timeout=60*5,max_queue=2000)
    pipe.attach(OOSAnalyzer)
    pipe.drain()

    
if __name__ == '__main__':
    main()

#keys in tmch_data
#'run': 4599, 'udp_sequence_number': 0, 'utc_seconds': 1612170501, 'nanoseconds': 900000000, 'dom_id': 808996919, 'dom_status_0': 2147483648, 'dom_status_1': 0, 'dom_status_2': 0, 'dom_status_3': 0, 'pmt_rates': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0#, 0.0, 0.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0, 5080.0], 'hrvbmp': 0, 'flags': 3, 'version': 2, 'yaw': 62.8602409362793, 'pitch': -0.006553844548761845,# 'roll': -0.0022368065547198057, 'A': (-0.0007436396554112434, 7.417984306812286e-06, -1.0075663328170776), 'G': (0.0, 0.31722140312194824, 1.4831897020339966), 'H': (0.07818181812763214, -0.10393939167261124, 0.12090909481048584), 'temp': 39.04, 'humidity': 1#2.85, 'tdcfull': 0, 'aesfull': 0, 'flushc': 0, 'ts_duration_ms': 100000}
