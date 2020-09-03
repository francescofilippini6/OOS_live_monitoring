#!/bin/bash

TARGET=~/analysis/
#PROCESSED=~/processed/prog1 & prog2 && fg

python Live_delay_display.py &
inotifywait -m -e create -e moved_to --format "%f" $TARGET | while read FILENAME
do
    echo Detected $FILENAME 
    scp /home/analysis/$FILENAME root@fcmserver2.bo.infn.it:/home/oos_web_root/data/IMAGES/ && ssh root@fcmserver2.bo.infn.it ln -f /home/oos_web_root/data/IMAGES/$FILENAME /home/oos_web_root/data/IMAGES/latest
done &

