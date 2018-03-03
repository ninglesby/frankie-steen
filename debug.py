import logging
import os
import time

import RPi.GPIO as GPIO
import Adafruit_ADS1x15
import pigpio

import config
import physical_control_v2 as physical_control
import interface_v2 as interface



pi = pigpio.pi()

frankies_log = interface.FrankiesLog().logger


stepper_sprocket_01 = physical_control.Stepper(pi=pi,
                                            logger=frankies_log,
                                            dir_pin=config.GPIO_STEPPER_0_DIR,
                                            on_pin=config.GPIO_STEPPER_0_ON,
                                            step_pin=config.GPIO_STEPPER_0_STEP,
                                            mode0_pin=config.GPIO_STEPPER_0_MODE0,
                                            mode1_pin=config.GPIO_STEPPER_0_MODE1,
                                            mode2_pin=config.GPIO_STEPPER_0_MODE2 )

stepper_sprocket_02 = physical_control.Stepper(pi=pi,
                                            logger=frankies_log,
                                            dir_pin=config.GPIO_STEPPER_2_DIR,
                                            on_pin=config.GPIO_STEPPER_2_ON,
                                            step_pin=config.GPIO_STEPPER_2_STEP,
                                            mode0_pin=config.GPIO_STEPPER_2_MODE0,
                                            mode1_pin=config.GPIO_STEPPER_2_MODE1,
                                            mode2_pin=config.GPIO_STEPPER_2_MODE2 )

try:
    for x in range(1):

        stepper_sprocket_01.change_step_res(config.STEPPER_FLOATS[3])
        stepper_sprocket_02.change_step_res(config.STEPPER_FLOATS[3])

        stepper_sprocket_01.advance_frame()
        
        if stepper_sprocket_01.current_mode != "STEPPER":

            stepper_sprocket_01.stop = False

            stepper_sprocket_01.current_mode = "STEPPER"

            if stepper_sprocket_01.logger:
                stepper_sprocket_01.logger.debug("Stepper mode enabled.")
            else:
                print "Stepper mode enabled."

        if not stepper_sprocket_01.stop and stepper_sprocket_01.steps:

            stepper_sprocket_01.turn_on()
            stepper_sprocket_02.turn_on()
            
            if stepper_sprocket_01.rewind:

                stepper_sprocket_01.pi.write(stepper_sprocket_01.dir_pin, not stepper_sprocket_01.default_dir)

            else:

                stepper_sprocket_01.pi.write(stepper_sprocket_01.dir_pin, stepper_sprocket_01.default_dir)


            for step in range(stepper_sprocket_01.steps):

                if not stepper_sprocket_01.stop:

                    stepper_sprocket_01.one_step()
                    stepper_sprocket_02.one_step()


    stepper_sprocket_01.turn_off()
    stepper_sprocket_02.turn_off()

except KeyboardInterrupt:

    stepper_sprocket_01.turn_off()
    stepper_sprocket_02.turn_off()