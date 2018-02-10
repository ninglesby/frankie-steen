#!/bin/bash

####DEPENDENCIES INSTALL

###ADC(analog to digital converter)

sudo apt-get update
sudo apt-get install build-essential python-dev python-smbus python-pip
sudo pip install adafruit-ads1x15