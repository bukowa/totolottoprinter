#!/bin/bash

USER=buk
IP=192.168.0.179

scp udev $USER@$IP:/home/$USER/udev
scp udev-rasp.sh $USER@$IP:/home/$USER/udev-rasp.sh