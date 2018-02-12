import logging
import os
import time

import RPi.GPIO as GPIO
import Adafruit_ADS1x15

import config
import physical_control
import interface


class Cleanup():

    def __init__(self, logger):

        self.cleanup_list = []
        self.logger = logger

    def clean_all(self):

        for item in self.cleanup_list:

            self.logger.info("Cleaning up %s" % item.__class__.__name__)

            item.cleanup()

        self.logger.info("Cleanup Complete")

        return True


def main():
    #initialize 4 channel 16-bit analog to digital converter
    adc = Adafruit_ADS1x15.ADS1115()

    # Create an instance of the logger
    frankies_log = interface.FrankiesLog().logger

    
    cleaner = Cleanup(frankies_log)
    #set gpio mode status, doesn't return anything if it was successful 
    #returns message if there is an error.
    gpio_mode_status = interface.set_gpio_mode()

    status = interface.Status(frankies_log)
    cleaner.cleanup_list.append(status)

    frankies_log.info("Initializing status object")
    status.nominal() # set status to nominal


    knob_select = physical_control.Knob(   pin=config.ADC_KNOB_0, adc=adc, mode=config.ADC_KNOB_SELECT, selections=10 )
    cleaner.cleanup_list.append(knob_select)


    try:

        while True:

            print knob_select.get_selection()

            time.sleep(.01)

    except KeyboardInterrupt:

        GPIO.cleanup()

if __name__ == "__main__":

    main()