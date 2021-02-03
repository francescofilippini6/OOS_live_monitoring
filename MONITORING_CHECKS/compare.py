import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import matplotlib as ppp
import warnings
from matplotlib.dates import DateFormatter, AutoDateLocator
plt.rcParams['axes.grid']=True
tmch_df = pd.read_csv('12-min-TMCH_Data_parsed')
srp_df = pd.read_csv('merged_srp.csv')

tmch_datetimes=[]
srp_datetimes=[]
for n in tmch_df['time(s)']:
    datetime_tmch_obj = datetime.datetime.strptime(n,'%H:%M:%S')
    tmch_datetimes.append(datetime_tmch_obj)

for n in srp_df['time']:
    datetime_srp_obj = datetime.datetime.strptime(n,'%H:%M:%S')
    srp_datetimes.append(datetime_srp_obj)

tmch_df['datetime'] = pd.Series(tmch_datetimes)
srp_df['datetime'] = pd.Series(srp_datetimes)



doms_list = np.unique(tmch_df['DOM'])

for i in range(5,6):
    tmch_data = tmch_df[tmch_df['DOM']==i]
    srp_data = srp_df[srp_df['DOM']==i]
    subscription_rate = 1/10
    tmch_rate = 1 #1 value/s
    expected_srp  = (max(srp_data['datetime'])-min(srp_data['datetime'])).total_seconds()*subscription_rate +1
    expected_tmch  = (max(tmch_data['datetime'])-min(tmch_data['datetime'])).total_seconds()*tmch_rate +1
    fig=plt.figure(figsize=(20,10))
    fig.suptitle('DOM_'+str(i))
    print("DOM",i)
    for index,key in enumerate(srp_df.keys()[-15:]):
        if expected_srp != len(srp_data[key]):
            #print(len(srp_data[key]))
            print(str(key)+': mismatch between expected ({0}) and observed ({1}) srp measures found!'.format(str(expected_srp),str(len(srp_data[key]))))
        if expected_tmch != len(tmch_data[key]):
            print(str(key)+': mismatch between expected ({0}) and observed ({1}) tmch measures found!'.format(str(expected_tmch),str(len(tmch_data[key]))))
            #print(len(tmch_data[key]))
        axx=fig.add_subplot(3,5,index+1)
        srp_data.plot(kind='scatter',x='datetime',y=key,color='red',ax=axx,alpha=0.5,label='SRP')        
        tmch_data.plot(kind='scatter',x='datetime',y=key,color='blue',ax=axx,alpha=0.1,label='TMCH')        
        # aesthetic iomprovements 
        if index<10:
            axx.tick_params(axis='x',which='both',bottom=False,top=False,labelbottom=False)
            axx.set_xlabel(' ')

        else:
            axx.set_xlabel('time (s)',fontsize=6)
            axx.tick_params(axis='x',labelsize=6)
            #  axx.xaxis.set_major_locator(plt.MaxNLocator(2))
            axx.xaxis.set_major_locator(AutoDateLocator())
            axx.xaxis.set_major_formatter(DateFormatter(' %H:%M:%S'))
            plt.setp(plt.gca().get_xticklabels(),rotation=90,horizontalalignment='right')

        axx.tick_params(axis='y',labelsize=6)           
        axx.set_ylabel(str(key),fontsize=6)
        axx.set_title(str(key), fontsize=10)
        axx.grid() 
        axx.legend()
   
    fig.tight_layout()
    fig.savefig('/home/km3net/analysis/MONITORING_CHECKS/Images/DOM_'+str(i)+'.png')
    


