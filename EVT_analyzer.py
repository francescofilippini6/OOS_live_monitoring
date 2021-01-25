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
        #self.delays=[]
        self.numberofactivedom=0
        
    
    def process(self,blob):
    
        #TMCH only for monitoring channel
        #tmch_data = kp.io.daq.TMCHData(io.BytesIO(blob['CHData']))
        #print(blob.keys())
        height=[]
        time =[]
        event_hits = blob['Hits']
        #event_hits = blob['TSHits']
        #print(event_hits)
        dom_id = np.unique(event_hits['dom_id'])
        for counter,dom in enumerate(self.orderedDOM):
            #for cycle for selecting the triggering DOMs                                                                                                                                                                                                    
            dom_height=65+36*counter
            print('DOM_id',self.Dom_id_name[str(dom)])
            print('height',dom_height)
            selected_dom=event_hits[event_hits['dom_id']==dom]
            #for cycle only on the channel_id triggered                                                                                                                                                                                                         
            for pmt in event_hits[event_hits['dom_id']==dom].channel_id:
                channel=selected_dom[selected_dom.channel_id == pmt]
                print('pmt'+str(pmt),channel.time)
                time.append(channel.time[0])
            height.append(dom_height)
        print(time,height)
        #plt.plot(time,height)
        #plt.show()
        #sys.exit()
    def finish(self):
        print("-------BYE BYE!! (As catom (dialatt arsan)-------)")
        
        
    
def main():
    pipe=kp.Pipeline()
    pipe.attach(kp.io.ch.CHPump , host='192.168.0.21', port=5553,tags='IO_EVT',timeout=60 * 5,max_queue=2000)
    #pipe.attach(kp.io.daq.TimesliceParser)
    pipe.attach(kp.io.daq.DAQProcessor)
    pipe.attach(OOSAnalyzer)
    pipe.drain()

    
if __name__ == '__main__':
    main()
