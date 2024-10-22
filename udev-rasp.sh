#!/bin/bash

USER=buk

sudo cp /home/$USER/udev /etc/udev/rules.d/99-escpos.rules
sudo udevadm control --reload
sudo service udev restart
sudo usermod -aG dialout $USER
sudo reboot
