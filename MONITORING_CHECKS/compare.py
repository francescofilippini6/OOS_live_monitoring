import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

tmch_df = pd.read_csv('12-min-TMCH_Data_parsed')
srp_df = pd.read_csv('datalog_parsed.csv')

doms_list = np.unique(tmch_df['DOM'])
#print(tmch_df.keys()[-14:])
for i in doms_list:
    tmch_data = tmch_df[tmch_df['DOM']==i]
    srp_data = srp_df[srp_df['DOM']==i]
    fig=plt.figure()
    fig.suptitle('DOM_'+str(i))
    for index,key in enumerate(tmch_df.keys()[-14:]):
        axx=fig.add_subplot(3,5,index+1)
        srp_data.plot(kind='scatter',x='time',y=key,color='red',ax=axx)
        tmch_data.plot(kind='scatter',x='time(s)',y=key,color='blue',ax=axx)
        
        axx.xaxis.set_major_locator(plt.MaxNLocator(2))
        if index<10:
            axx.tick_params(axis='x',which='both',bottom=False,top=False,labelbottom=False)
            axx.set_xlabel(' ')

        else:
            axx.set_xlabel('time (s)',fontsize=6)
            axx.tick_params(axis='x',labelsize=6)

        axx.tick_params(axis='y',labelsize=6)           
        axx.set_ylabel(str(key),fontsize=6)
        axx.set_title(str(key), fontsize=10)
        #axx.label_outer()
        #axx.set_ylabel(" ")
        
        #if index != 13:
        #    axx.set_xlabel(" ")
        
    fig.tight_layout()
    fig.savefig('DOM_'+str(i)+'.png')
    
    

#print(tmch_df.head(100))
#print(srp_df.head(10))
