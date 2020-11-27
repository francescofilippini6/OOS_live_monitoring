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
        
        event_hits = blob['Hits']
        dom_id = np.unique(event_hits['dom_id'])
        y=[]
        t=[]
        height=[]
        #print(event_hits.time)
        mean_triggered_time = np.mean(event_hits.time)
        #reading the offset time from detx file
        #if len(dom_id)>9:
        #    print("calibration")
        #    return blob
        if 808971330 not in dom_id:
            return blob
        calibration_offset = self.calibration_file_reader()          
        print(calibration_offset)

        for counter,dom in enumerate(self.orderedDOM):
        #for cycle for selecting the triggering DOMs
            dom_height=65+36*counter
            #if dom in dom_id:
            #self.Dom_id_name[str(dom)] 
            print('DOM_id',dom)
            selected_dom=event_hits[event_hits['dom_id']==dom]
            #for cycle only on the channel_id triggered
            for pmt in event_hits[event_hits['dom_id']==dom].channel_id:
                channel=selected_dom[selected_dom.channel_id == pmt]
                print (channel.time)
                #SMALL octoPAES
                dom_row=calibration_offset[calibration_offset['DOMnumber']==self.Dom_id_name[str(dom)]]
                #print(dom_row)
                if pmt < 12:
                    small_offset=dom_row[dom_row['channel']==0]['deltaT'].values[0]
                    print("SMALL:",small_offset)
                    t.append(channel.time[0]-mean_triggered_time+small_offset)
                    #t.append(0)
                    height.append(dom_height)
                
                else:
                    large_offset=dom_row[dom_row['channel']==12]['deltaT'].values[0]
                    print("LARGE:",large_offset)
                    t.append(channel.time[0]-mean_triggered_time+large_offset)
                    #t.append(0)
                    height.append(dom_height)
                    
                #for j in event_hits[event_hits['dom_id']==dom].time:
                #y.append(self.Dom_id_name[str(i)])
                #
            #else:
            #t.append(0)
            #height.append(dom_height)
            #NEED to calibrate the hits with the t0 offset in the detector file!!!!
                
        print(event_hits)
            
        print('\n')
        print('\n')

    
        print(height,t)
        
        
        #-----------------------------------------
        #producing the 2d-histogram z-t 
        #still missing the recentering of the time and the fixing of the dimensions!! (18x280)
        #-----------------------------------------
        pos_z_edges = np.linspace(47, 695, 19)
        time_edges = np.linspace(-200, 1200, 281) 
        
        #x-y inverted due to matche the image dimension of the NN 
        array=plt.hist2d(height,t,bins=(pos_z_edges,time_edges))        
        
        #reshaping of the image in order to fit the input of the NN
        #print(array[0].shape)
        np.savetxt('event_image.txt',np.array(array[0]))
        image = array[0].reshape(1,18,280,1)
        print(image.shape)
        print(len(array[0][0]))
        
        #H = np.histogram2d(t,height,bins=(time_edges, pos_z_edges))
        #H = np.histogram2d(height,t,bins=(pos_z_edges,time_edges))
        
        #img=plt.imshow(H[0],cmap="viridis",aspect='auto')#,origin='lower')
        #a=plt.hist2d(H)
        #H.savefig('histo2dnumpy.png')
        
        #-----------------------------------------
        #loading the model and weights of the NN and produce the regression
        #-----------------------------------------
        from keras.models import model_from_json
        #retrieving the model
        json_file = open('model.json','r')
        loaded_model_json = json_file.read()
        loaded_model = model_from_json(loaded_model_json)
        #retrieving the best weights obtained during training
        loaded_model.load_weights("best_model.hdf5")
        loaded_model.compile(optimizer='adam',loss='mean_squared_error')
        y=(180/np.pi)*np.arccos(loaded_model.predict(image))
        print("Predicted value of the angle:", y)
        
        #-----------------------------------------
        
        #2d histogram pltted
        imageshow=plt.hist2d(t,height,bins=(time_edges,pos_z_edges))        
        plt.ylabel('z')
        plt.xlabel('time')
        plt.title('z-t plane image')
        plt.savefig('hist.png')
        
        sys.exit()
        
        
    def calibration_file_reader(self):          
        delays = pd.read_csv('calibration.csv')                                                                              
        #print(delays['deltaT'])                                                                                    
        return delays
        
    def finish(self):
        print("-------BYE BYE!! (As catom (dialatt regian)-------)")
        
        
    
def main():
    pipe=kp.Pipeline()
    pipe.attach(kp.io.ch.CHPump , host='192.168.0.21', port=5553,tags='IO_EVT',timeout=60 * 5,max_queue=2000)
    pipe.attach(kp.io.daq.DAQProcessor)
    pipe.attach(OOSAnalyzer)
    pipe.drain()

    
if __name__ == '__main__':
    main()
