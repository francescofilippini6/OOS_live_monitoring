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
from km3pipe.core import Pump
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

class OOSAnalyzer(Module):
    def configure(self):
        self.orderedDOM = [806451575,808981684,808447031,808985194,808971330,800000000,806451239,808952022,808967370,808489098,808976266,809537142,808984748,808982228,808980464,808976292,809544159,808996919]
        self.decimal = list(range(1, 19)) 
        self.Dom_id_name = {str(self.orderedDOM[i]) : self.decimal[i] for i in range(len(self.orderedDOM))}
        #print(self.Dom_id_name)
        self.doms=[]
        self.TOOS=0
        self.numberofactivedom=0
        self.status=0
        self.timetoplot=60
        self.final_delay=0
        self.testdf=pd.DataFrame(columns=['Time','DOMnumber','channel', 'deltaT'])        
        self.SUMMARY=pd.DataFrame(columns=['dateandTime','DOMName', 'MEAN', 'MAX','MIN'])
    
    def process(self,blob):
        info = blob['TimesliceInfo']
        info2=blob['TimesliceFrameInfos']
        #print(blob.keys)
        TSindex=info['timestamp'][0]
        Time = info['nanoseconds'][0]/1000000000
        TSCounter = TSindex+Time
        print ('TSCounter %d' % TSCounter, end='\r')
        self.status=0
        #TAKING 1 TS EACH MINUTE
        if Time==0.1 and TSindex%60==0:
            tshits = blob['TSHits']
            self.doms = np.unique(tshits['dom_id'])
            self.numberofactivedom = len(self.doms)
            #fixing DOM 1 LARGE 
            dom1=tshits[tshits.dom_id==806451575]
            pmt1_3 = dom1[dom1.channel_id == 12]
           
            #cycle over the remaining 16 DOMS 
            now = datetime.now()
            for i in self.orderedDOM:
                if i == 800000000:
                    #to skip DOM 6
                    continue
                if i == 806451575:
                    OPtype=[0]
                else:
                    OPtype=[0,12]
                dom2=tshits[tshits.dom_id == i]
                #fixing for all the LARGE Board
                for chan in OPtype:
                    pmt1_dtype = dom2[dom2.channel_id == chan]
                    delay_over_TS=[]
                    for t in pmt1_3.time:
                        for tt in pmt1_dtype.time:
                            deltat=tt-t
                            delay_over_TS.append(deltat)
                
                
                    #print(len(delay_over_TS))
                    #print(delay_over_TS)
                    
                    #calculate the mean of a symmetric bound set around zero
                    value=[]
                    for x in delay_over_TS:
                        if x > -7000 and  x < 7000:
                            value.append(x)
                            self.final_delay=round(np.mean(value))
                    print('-.-.-.-.-.-.-.-.-.-.-.-')
                    print("len",len(value))
                    #print("values",value)
                    Dom_numbers= self.Dom_id_name[str(i)] #putting decimal dom number
                    print('DOM_'+str(chan)+'_'+str(Dom_numbers)+':',self.final_delay)
                    #Implementig circular buffer on python dataframe
                    self.testdf.loc[len(self.testdf)+1] = [TSCounter, Dom_numbers,chan, self.final_delay]
                    self.testdf.to_csv('calibration.csv', index=False)
            sys.exit()
            return blob
            
            #self.over_threshold()
            
            
            #plot at each hour if OOS not occurred                                                                                                                                                      
            # if TSindex%3600==0:
            #   self.plotter()
            #else:
            #return blob
    
    def over_threshold(self):
        #Threshold delays (1 micro, 100 ns, 50 ns)
        if abs(self.final_delay) > 1000:
            Over1micro = self.testdf.loc[len(self.testdf)].to_csv('Over1micro.csv',mode='a',header=False) 
            self.status=1
        elif abs(self.final_delay) > 100:
            Over100nano = self.testdf.loc[len(self.testdf)].to_csv('Over100nano.csv',mode='a',header=False) 
            self.status=1
        elif abs(self.final_delay) > 50:
            Over50nano = self.testdf.loc[len(self.testdf)].to_csv('Over50nano.csv',mode='a',header=False) 
            self.status=1
    
    def summary(self):
        #le calcoliamo come valore di riferimento sulle prime N TS, poi li possiamo aggiornare per printare                          
        df_dom = self.testdf[(self.testdf.DOMnumber == i)]
        MEAN = df_dom["deltaT"].mean()
        MAX =  df_dom["deltaT"].max()
        MIN =  df_dom["deltaT"].min()
        domname = 'DOM'+str(i+1)
        self.SUMMARY.loc[len(self.SUMMARY)+1] = [now,domname, MEAN, MAX,MIN]

    def plotter(self):
        now = datetime.now()
        df_list = []
        missing_dom=16-self.numberofactivedom
        name=[]
        Dom_number=[]
        for j in self.doms:
            Dom_number.append(self.Dom_id_name[str(j)]) #getting the doms in decimal base
        
        Dom_number.sort()
        Dom_number=Dom_number[1:]
        print(Dom_number)
        for aa in Dom_number:
            partial = self.testdf[(self.testdf.DOMnumber == aa)].tail(60)
            name.append('CLB_'+str(aa))
            # make a list of all dataframes in order                             
            df_list.append(partial)
        if missing_dom!=0:    
            for i in range(missing_dom):
                partial = self.testdf[(self.testdf.DOMnumber == 1)].tail(60)
                df_list.append(partial)
                name.append('CLB_'+str(1))
        #start of the PLOT with 16 subplots
        time = now.strftime("%y_%m_%d_%H_%M")
        
        fig = plt.figure(figsize=(10, 8))
        outer = gridspec.GridSpec(4, 4, wspace=0.3, hspace=0.3)
        for i in range(16):
            inner = gridspec.GridSpecFromSubplotSpec(1, 2,subplot_spec=outer[i], wspace=0.1, hspace=0.1)
            axe = plt.Subplot(fig,inner[0])
            if i<12:
                axe.set_xticks([])
            l=df_list[i].plot(x ='Time', y='deltaT', kind='scatter', ax=axe)
            axe2 = plt.Subplot(fig, inner[1])
            axe2.tick_params(colors='red')
            if i==3 or i == 7 or i == 11 or i == 15:
                axe2.yaxis.tick_right()
                #axe2.tick_params(right=True, labelright=True,colors='red')
            else:
                axe2.set_yticks([])
            
            g=self.testdf[(self.testdf.DOMnumber == Dom_number[i])].hist(column='deltaT',ax=axe2,color = "red")
            fig.add_subplot(axe)
            fig.add_subplot(axe2)
            titlename = name[i]
            axe.set_title(titlename)
            axe.set_xlabel('')
            axe.set_ylabel('')
            axe2.set_title('')
            if i==0:
                axe.set_ylabel('Delay (ns)')
            elif i==15:
                axe2.set_xlabel('TIME (s)')
            
        fig.suptitle('DELAYS_referred_CLB1_at:'+time,y=0.05,x=0.5)
        namefigure="Plot16DOMS_"+time
        fig.savefig(namefigure)
      
    def finish(self):
        #self.plotter()
        print("killed CTRL_C")
    

    
    
def main():
    pipe=kp.Pipeline()
    pipe.attach(kp.io.ch.CHPump,host='192.168.0.21', port=5553,tags='IO_TSL0',timeout=60 * 5,max_queue=2000)
    pipe.attach(kp.io.daq.TimesliceParser)
    pipe.attach(OOSAnalyzer)
    pipe.drain()

    #/////to store the last 3h dataframe into a hdf5 file/////
    #store = HDFStore('self.SUMMARY_LAST3H.h5')
    #store.put('self.testdf',self.testdf)
    #store.close()

if __name__ == '__main__':
    main()
