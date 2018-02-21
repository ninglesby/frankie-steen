import logging
import os
import time

import RPi.GPIO as GPIO
import Adafruit_ADS1x15
import pigpio

import config
import physical_control_v2 as physical_control
import interface_v2 as interface



class Cleanup():

    def __init__(self, logger):

        self.cleanup_list = []
        self.logger = logger

    def clean_all(self):

        for item in self.cleanup_list:

            self.logger.info("Cleaning up %s" % item.__class__.__name__)

            item.cleanup()

        self.logger.info("Cleanup Complete")

        return


def main():

    #initialize 4 channel 16-bit analog to digital converter
    adc = Adafruit_ADS1x15.ADS1115()

    # Create an instance of the logger
    frankies_log = interface.FrankiesLog().logger

    
    cleaner = Cleanup(frankies_log)
    #set gpio mode status, doesn't return anything if it was successful 
    #returns message if there is an error.

    # Output logger info
    frankies_log.info("Starting up the frankie_steen")

    stepper_sprocket = physical_control.Stepper(logger=frankies_log,
                                                dir_pin=config.GPIO_STEPPER_0_DIR,
                                                on_pin=config.GPIO_STEPPER_0_ON,
                                                step_pin=config.GPIO_STEPPER_0_STEP,
                                                mode0_pin=config.GPIO_STEPPER_0_MODE0,
                                                mode1_pin=config.GPIO_STEPPER_0_MODE1,
                                                mode2_pin=config.GPIO_STEPPER_0_MODE2 )

    knob_spring = physical_control.Knob(   pin=config.ADC_KNOB_1, adc=adc, mode=config.ADC_KNOB_SWEEP, sweep_range=[-1,1] )

    knob_select = physical_control.Knob(   pin=config.ADC_KNOB_0, adc=adc, mode=config.ADC_KNOB_SELECT, selections=2 )
    
    blue_light = interface.Light(   logger=frankies_log,
                                    light_pin=config.GPIO_STATUS_BLUE,
                                    )

    last_warning = ""
    try:

        while True:

            if stepper_sprocket.energized:
                blue_light.set_light(mode="BLINK", blink_speed=0)

            else:

                blue_light.set_light(mode="CONSTANT")

            if knob_select.get_selection() == 1:
                
                stepper_sprocket.change_step_res("1/8")
                stepper_sprocket.advance_frame()
                stepper_sprocket.stepper()


                frame_count, lifetime_frame_count = physical_control.increment_frame_count()

                frankies_log.info("Captured Frame: %s. Lifetime Capture: %s Frames" % (str(frame_count), lifetime_frame_count))

                time.sleep(.5)

            #print stepper_sprocket.steps

            #blue_light.set_light(mode="BLINK", blink_speed=0)

            elif knob_select.get_selection() == 2:
            
                stepper_sprocket.set_speed(knob_spring.get_value())
                
                stepper_sprocket.motor()

            else:

                if last_warning != "Invalid Selection":

                    last_warning = "Invalid Selection"
                    frankies_log.warning("%s is an invalid selection" % str(knob_select.get_value()))

            time.sleep(.02)

            #blue_light.set_light(mode="CONSTANT")

    except KeyboardInterrupt:

        stepper_sprocket.turn_off()


if __name__ == "__main__":

    main()