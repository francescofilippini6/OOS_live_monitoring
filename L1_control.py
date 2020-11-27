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

class OOSAnalyzer(Module):
    def configure(self):
        self.orderedDOM = [806451575,808981684,808447031,808985194,808971330,800000000,806451239,808952022,808967370,808489098,808976266,809537142,808984748,808982228,808980464,808976292,809544159,808996919]
        self.decimal = list(range(1, 19)) 
        self.Dom_id_name = {str(self.orderedDOM[i]) : self.decimal[i] for i in range(len(self.orderedDOM))}
        self.doms=[]
        self.times=[]
        self.numberofactivedom=0
        
    
    def process(self,blob):
        #print(blob)
        info = blob['TimesliceInfo']
        info2=blob['TimesliceFrameInfos']
        #print("Timesliceinfo", info)
        #print("frame",info2)
        #print("TimesliceinfoFrameInfos",info2.keys)
        TSindex=info['timestamp'][0]
        Time = info['nanoseconds'][0]/1000000000
        TSCounter = TSindex+Time
        self.times.append(TSCounter)
        #print("NOW",datetime.utcnow())
        
        tshits = blob['TSHits']
        self.doms = np.unique(tshits['dom_id'])
        #print ('TSCounter %d' % TSindex, end='\r')
        #timesliceframeinfo contiene dom_id, run_id,
        timestamps=[]
        for i in self.doms:
            timestamps.append(info2[i]['timestamp'][0])
        
        #print('domtimestamp',timestamps)
        #print('tsinfotimestamp', TSindex)
        
        #print("Time:",TSCounter)
        #if a == 808981684: 
        #self.TOOS=TSCounter
        #a=808971330
        a=808985194
        if a in self.doms:
            self.numberofactivedom = len(self.doms)
            for iii in self.doms:
                print("Dom_length", self.Dom_id_name[str(iii)])
            #for ab in self.doms:
            #    print(self.Dom_id_name[str(ab)])
            
            #print(TSCounter)
            dom=tshits[tshits.dom_id == a]
            #pmt0=dom[dom.channel_id == 0]
            print(dom.channel_id)
            #for iaa in range(1,31):
            #pmt12=dom[dom.channel_id == 12]
            
            #diff=pmt0.time-pmt12.time
            #print('pmt.time0', pmt0.time)
            #print('pmt.time12', pmt12.time)
            #print("length",len(pmt0.time))
        #print('pmt diff time',diff)
        #print("out of TS")
        #for ia in range(0,31):
        #print(ia)
        #    pmt=dom[dom.channel_id == ia]
        #    print("channel",ia]
        #    print("time hit:",len(pmt.time))
        #print(len(pmt.time))
        
        #sys.exit()
        #print(TSCounter)        
        #self.status.append(TSCounter)

    def finish(self):
        print(self.times)
        print("--------------")
        print(self.times.sort())

    
    
def main():
    pipe=kp.Pipeline()
    pipe.attach(kp.io.ch.CHPump , host='192.168.0.21', port=5553,tags='IO_TSL2',timeout=60 * 5,max_queue=2000)
    pipe.attach(kp.io.daq.TimesliceParser)
    pipe.attach(OOSAnalyzer)
    pipe.drain()

    #/////to store the last 3h dataframe into a hdf5 file/////
    #store = HDFStore('self.SUMMARY_LAST3H.h5')
    #store.put('self.testdf',self.testdf)
    #store.close()

if __name__ == '__main__':
    main()
