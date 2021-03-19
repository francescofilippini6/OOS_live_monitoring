#!/usr/bin/env python
# coding=utf-8
# vim: ts=4 sw=4 et

# Original Author: Alba Domi - COPYRIGHT 2018
# Modified by T. Chiarusi 2018, 2019/04/24 Francescos
# Compatible with KM3PIPE 9 beta

import signal
import sys
import subprocess

import collections
from collections import defaultdict
import io
import os
import time
import km3pipe as kp
import numpy as np
from km3pipe.io.daq import TMCHData
from km3pipe import Module
#from km3pipe.core import Pump
from datetime import datetime

log = kp.logger.get_logger("udpAnalyser")
#db = kp.db.DBManager()
#det_id = 29

UDP_RATE_PER_DOM = 10  # Hz
LIMIT_TIME_SYNC  = 60    #3701 # .5  # s   value tuned after several trials (3700 trigger the warning printing)
TIME_OFFSET = 0 # 32.0481 # s

class UDPAnalyser(Module):

    def configure(self):

      # self.detector = self.require("detector")
        self.detector_oid = 4 #db.detectors[db.detectors.SERIALNUMBER == det_id].OID.iloc[0]

        self.interval = 1  # 10 seconds
        self.run_id = defaultdict(int)
        self.timestamp = defaultdict(int)
        self.udp_counts = defaultdict(int)
        self.total_number_udps = defaultdict(int)
        self.data_time = defaultdict(int)
        self.start_running = defaultdict(int)
        self.start_of_run_dom = defaultdict(int)
        self.end_of_run_dom = defaultdict(int)
        self.run_duration_dom = defaultdict(int)
        self.times = defaultdict(list)

        self.total_error_udp_missing = defaultdict(int)
        self.total_ms_time_desync_count = defaultdict(int)
        self.total_error_data_machine_time = defaultdict(int)

        self.filename = ""
        self.time_run_change = 0

        #----------------------------------------------------------------
        #conversion dom_id to dom_number for  phase2 @BCI
        #----------------------------------------------------------------
       # self.orderedDOM = [818798894,818845349,818848239,818798906,818848226,818798740.818806250,818785829,818806263,818785853,818798725,818848646,818798728,818798885,818848251,818845350,818785841,818806251]
       
        self.orderedDOM = [806472270,806451575,808981684,808447031,808985194,808971330,808982053,806451239,808952022,808967370,808489098,808976266,809537142,808984748,808982228,808980464,808976292,809544159,808996919]

        self.decimal = list(range(0, 19))
        self.Dom_id_name = {str(self.orderedDOM[i]) : self.decimal[i] for i in range(len(self.orderedDOM))}
        self.doms=defaultdict(int)


    def process(self, blob):
        
        arrival_time = blob["CHPrefix"].timestamp 
        
        tmch_data = kp.io.daq.TMCHData(io.BytesIO(blob['CHData']))    
                                       
        dom_id = tmch_data.dom_id
        
        
        #-----------------------------------------------------------------
       #if self.Dom_id_name[str(dom_id)]==18: #to select a specific dom to print
            #print("DOM_",self.Dom_id_name[str(dom_id)])
            #print("DOM %d , timestamp %d",dom_id, self.timestamp[dom_id])
            #print("arrival_time",arrival_time)
            #print("supernova time",time.time())       
            #print('date_time in seconds',tmch_data.utc_seconds)
       # if dom_id not in self.detector.doms:
          # return blob
       
        #----------------------------------------------------------------
        if not self.start_of_run_dom[dom_id]:  #for the 1st run, initialize the start time in seconds for each DOM. For subsequent run this is done at run change
             self.start_of_run_dom[dom_id] = (tmch_data.utc_seconds*1e9 + tmch_data.nanoseconds)*1e-9  
   
        if not self.timestamp[dom_id]: #enter here at first round and assign value to timestamp[dom_id] and udp_counts[dom_id]; timestamp is increased by 10 s, it's the interval time
            self.reset_data(dom_id)

        if not self.run_id[dom_id]: #fill run_id dictionary with run values;@ 1st timeslice per DOM of the run it enters here (run_id = 0) then id is associated and never enters here until run change
            self.run_id[dom_id] = tmch_data.run
        
        if self.filename == "":
            self.filename = "test_monitoring_times_RUN" + str(tmch_data.run) + ".csv"
            self.write_header(tmch_data.run)
            print(self.filename)
        #----------------------------------------------------------------
        self.total_number_udps[dom_id] += 1 #used to count the total number of udp packets, never reset
        self.udp_counts[dom_id] += 1 #counts the number of udp packets since it is incremented every time a packet is detected; this is reset to 0 every self.interval seconds, used to check packet loss in the interval
        #----------------------------------------------------------------
        total_time = (tmch_data.utc_seconds*1e9 + tmch_data.nanoseconds)*1e-6  # ms
        if self.Dom_id_name[str(dom_id)]==17:
            print("packet time ",tmch_data.utc_seconds,' ',tmch_data.nanoseconds)
        self.times[dom_id].append(total_time) 
        #----------------------------------------------------------------
        #if self.Dom_id_name[str(dom_id)]==18:
            #print("TIMES",self.times[dom_id])
            #print("total_time",total_time)
        #----------------------------------------------------------------
        if self.return_timedelta(dom_id) > self.interval:    #interval=10 s
            """
            Every self.interval it checks the packet loss and the ms time synchronization.
            """
            if self.start_running[dom_id] == 0:
                self.start_running[dom_id] = 1
            self.check_packet_loss(dom_id)
            self.check_100ms_sync(dom_id)
            self.reset_data(dom_id)
        #----------------------------------------------------------------
        #keep ATTENTION to the difference between data_time(s) and times(ms)
        self.data_time[dom_id] = tmch_data.utc_seconds
        
        #----------------------------------------------------------------
        #function execution > check done for each dom for each TS
        self.check_data_machine_time(arrival_time,dom_id)
        #----------------------------------------------------------------
        #run number changing triggers the writing on disk
        if tmch_data.run != self.run_id[dom_id]:
            if self.Dom_id_name[str(dom_id)]==17: #to select a specific dom to print        
                print("sono nel nuovo run ",tmch_data.run)
            self.end_of_run_dom[dom_id] = (tmch_data.utc_seconds*1e9 + tmch_data.nanoseconds)*1e-9 #in seconds; end of previous run = start of new run
            self.run_duration_dom[dom_id] = self.end_of_run_dom[dom_id] - self.start_of_run_dom[dom_id]         #duration of run for each dom, in seconds
            self.start_of_run_dom[dom_id] = (tmch_data.utc_seconds*1e9 
                                        + tmch_data.nanoseconds)*1e-9  # reinitialize the start of run for the new run; in seconds
            self.write_data_into_file(dom_id)
            self.reset_data_end_of_run(dom_id)
            self.time_run_change = self.timestamp[dom_id]
            if self.Dom_id_name[str(dom_id)]==17: #to select a specific dom to print        
                print("New Run ",tmch_data.run,"started at ",self.start_of_run_dom[dom_id])
        #----------------------------------------------------------------
        if self.time_run_change != 0:
            if (time.time() - self.time_run_change) > 300:  # when 300 seconds pass from last run change, cretaes the new file into which writing data for new run. if new run is shorter than 300 s, it is appended in the fi†s†cle of previous run
                self.filename = ""
                self.time_run_change = 0

        return blob
        
        #----------------------------------------------------------------
        #end of process function
        #----------------------------------------------------------------

        #def finish(self):
        #    print(self.orderedDOM)
        #    for i in self.orderedDOM:
        #        print(i)
        #        self.write_data_into_file(i)


     
    #----------------------------------------------------------------
    #making the difference of system time.time(s) and timestamp; timestamp changes every 10 s
    def return_timedelta(self, dom_id):
        return time.time() - self.timestamp[dom_id]
    #----------------------------------------------------------------
    def reset_data(self, dom_id): #called at the end of every self.interval
        self.times[dom_id].clear()
        self.udp_counts[dom_id] = 0 #reset to 0 every self.interval
        self.timestamp[dom_id] = time.time()
    #----------------------------------------------------------------
    def write_header(self, run_id):
        """
        This function is called once (if the outputfile doesn't exist).
        """
        if not os.path.exists(self.filename):
            out = open(self.filename, "w+")
            out.write("det_id\trun\tsource")
            out.write("\tTMCH_UDP_count_errors\tTMCH_UDP_time_duration_error\tTMCH_time_sync_error\tstart_of_run_sec\ttotal_number_udp_packets")
            out.write("\n")
            out.close()
    #----------------------------------------------------------------
    def check_packet_loss(self, dom_id):
        """
        Check if the effective number of packets received by each dom
        is different from what expected.
        """
        if self.Dom_id_name[str(dom_id)]==17:
            print("controllo i pacchetti del dom ", dom_id)
            print("start of run ",self.start_of_run_dom[dom_id])
            print('time of check ',time.time())
        n_expected_packets = self.interval * UDP_RATE_PER_DOM  #expected number of packets in interval time width
        if self.start_running[dom_id] == 1:
            if not (n_expected_packets - 1 <= self.udp_counts[dom_id] <= n_expected_packets + 1):   #expected packet \pm 1 why?
                if self.Dom_id_name[str(dom_id)]==17:                
                    log.warning("RUN {0} : Packet ratio for DOM {1}: {2}/{3} = {4}".format(self.run_id[dom_id], self.Dom_id_name[str(dom_id)], self.udp_counts[dom_id], n_expected_packets, self.udp_counts[dom_id]/n_expected_packets))
                self.total_error_udp_missing[dom_id] += 1 #increment by 1 every interval in which a difference expected/observed is found 
            else:
                if self.Dom_id_name[str(dom_id)]==17:
                   # print('start of run time for dom {0} - {1}: '.format(self.Dom_id_name[str(dom_id)],self.start_of_run_dom[dom_id]))                   
                   # print('time of packet loss check: ',time.time())
                    print('No packet losses within previous 1 second for DOM{0}: expected {2} - arrived {1}'.format(self.Dom_id_name[str(dom_id)],self.udp_counts[dom_id],n_expected_packets))
    #----------------------------------------------------------------
    def check_100ms_sync(self, dom_id): 
        """
        Check if there are some consecutive udp packets
        with delta_t != 100 ms. 
        """
        self.times[dom_id].sort()
        count = collections.Counter()
        for i,j in zip(self.times[dom_id][0::],self.times[dom_id][1::]):
            #print(j-i)
            if j-i != 100:  #if j-i i.e. timeslice_n - timeslice_n-1 different from 100 ms
                count[j-i] += 1
                self.total_ms_time_desync_count[dom_id] += 1
                #---------------------------------------------------------------
                if count:
                    log.error("{3} - {4} RUN {0} : udp packet duration != 100 ms ({2}) for DOM {1}!"
                              .format(self.run_id[dom_id], dom_id, j-i, datetime.timestamp(datetime.now()),datetime.now()))
                
    #----------------------------------------------------------------
    def check_data_machine_time(self, arrival_time, dom_id): #tempo arrivo con tempo del dato
        """
        Check if the timestamp of each udp packet and 
        its arrival time on the machine is > 1 minute.
        """
        dt = arrival_time - self.data_time[dom_id]+TIME_OFFSET
        #            print("{0}\t{1}\t{2}".format(datetime.timestamp(datetime.now()),datetime.now(),dt))
        if abs(dt) > 946080000: #if delay is larger than 30 years
            print('!CLOCK RESET!  packet time =',self.data_time[dom_id], 'VS arrival time on machine = ', arrival_time, ' for DOM ', self.Dom_id_name[str(dom_id)])
        elif abs(dt) > LIMIT_TIME_SYNC:
            self.total_error_data_machine_time[dom_id] += 1
            log.error("At {4} for RUN {0} : Packet time = {5} and arrival on machine time {3} not synchronized for DOM {1}: difference is dt = {2} s "
                      .format(self.run_id[dom_id], self.Dom_id_name[str(dom_id)], dt, arrival_time,datetime.now()),self.data_time[dom_id])
    #----------------------------------------------------------------
    def write_data_into_file(self, dom_id):
        print("DOM {}".format(self.Dom_id_name[str(dom_id)]))
        print("Time duration of run = {} s".format(self.run_duration_dom[dom_id]))
        print("Packets arrived: {0} VS expected: {1} . Packet fraction = {2} %".format(self.total_number_udps[dom_id],self.run_duration_dom[dom_id]*10,(self.total_number_udps[dom_id]/self.run_duration_dom[dom_id]*10)))
        out = open(self.filename, "a+")
        print("Dumping summary info for run: {} \n".format(self.run_id[dom_id]))
        out.write("{0}\t{1}\t{2}".format(self.detector_oid,self.run_id[dom_id],self.Dom_id_name[str(dom_id)]))
        udp_missing = self.total_error_udp_missing[dom_id]
        ms_time_desync = self.total_ms_time_desync_count[dom_id]
        data_machine_desync = self.total_error_data_machine_time[dom_id]
        out.write("\t{1}\t{2}\t{3}\t{4}\t{5}".format(self.Dom_id_name[str(dom_id)],
                                                            udp_missing, ms_time_desync,
                                                             data_machine_desync, 
                                                             self.start_of_run_dom[dom_id],
                                                             self.total_number_udps[dom_id]))
        out.write("\n")
        out.close()
    #----------------------------------------------------------------
    def reset_data_end_of_run(self, dom_id): #called only at the end of the run
        self.run_id[dom_id] = 0
        self.total_error_udp_missing[dom_id] = 0
        self.total_ms_time_desync_count[dom_id] = 0 
        self.total_error_data_machine_time[dom_id] = 0
        self.total_number_udps[dom_id] = 0
        self.times = defaultdict(list)
        self.udp_counts[dom_id] = 0
        self.timestamp[dom_id] = time.time()
    #----------------------------------------------------------------
def signal_handler(sig, frame):
        print('You pressed Ctrl+\!')
        print("\nMON quitting time: {0} - {1}\n".format(datetime.timestamp(datetime.now()),datetime.now()));
        #os.kill(0, signal.SIGINT)
        sys.exit(0)
    #----------------------------------------------------------------

def main():
    #detector = kp.hardware.Detector(det_id = 29)
    signal.signal(signal.SIGQUIT, signal_handler)
    print("\n---- Tom's modified udpAnalyser v1.0 ----\n")
    print("\nMON starting time: {0} - {1}".format(datetime.timestamp(datetime.now()),datetime.now()));
    print("\npress Ctrl+\ (SIGQUIT)for quitting gently and getting the stopping time.")
    pipe = kp.Pipeline(timeit=True)
    pipe.attach(kp.io.CHPump, host='192.168.0.21',
                              port=5553,
                              tags='IO_MONIT',
                              timeout=60*60*24*7,
                              max_queue=100000)
#    pipe.attach(UDPAnalyser, detector=detector)
    pipe.attach(UDPAnalyser)
  
    pipe.drain()
    
    

if __name__ == "__main__":
    main()
