# steps to produce the monitoring plots 

1. Launch the python program: python TMCH_dumper.py
2. put in run the string, with whatever runsetup
3. waiting for the end of the run

4srp. launch on the CU the command: mono DumpDataLog.exe /var/km3net/nfsshare/uploads/datalogs/#Date and time of the run#_DetectorManager.datalog > filename
5srp. copy it on supernova through scp commmand
6srp. parsing the file with the program: srp_parser.py (this will produce a .csv file)

4tmch. the point 1 at the end of the run stops its exectuion prodcing a csv file 

7 launch compare.py program to retrieve both srp and tmch data and make the plots
