import logging
import os
import time
from threading import Thread

import RPi.GPIO as GPIO
import Adafruit_ADS1x15
import pigpio

import config
import physical_control



import interface
import helpers


def btn_calibrate_cb0(pi):

    current_state = pi.read(config.GPIO_STATUS_BLUE)

    pi.write(config.GPIO_STATUS_BLUE, not current_state)
    
    print "Callback 0"

def btn_calibrate_n0(status):

    print "notifying"

    #status.display.mode="SCROLL" 
    #status.display.text.append("notify1")
    status.display.title="CALIBRATE PRESSED"

def btn_calibrate_cb1():
    
    print "Callback 1"

def btn_calibrate_n1(status):

    status.dispay.message(text=["notify2"], title="CALIBRATE PRESSED")



def main():

    #initialize pigpio object
    pi = pigpio.pi()

    #initialize 4 channel 16-bit analog to digital converter
    #adc = Adafruit_ADS1x15.ADS1115()

    #display = interface.Display()


    # Create an instance of the logger
    frankies_log = interface.FrankiesLog().logger

    #status = interface.Status(logger=frankies_log, display=display)

    
    '''
    #add a handler to the logger to output to the display
    sh = interface.ScreenHandler()
    sh.setLevel(config.LOG_SHELL_VERBOSITY)
    sh.set_display(display)


    simple_formatter =  logging.Formatter('%(message)s')
    sh.setFormatter(simple_formatter)
    frankies_log.addHandler(sh)
    '''
    
    cleaner = helpers.Cleanup(frankies_log)

    #cleaner.cleanup_list.append(display)


    # Output logger info
    frankies_log.info("Starting up the frankie_steen")

    stepper_sprocket_01 = physical_control.Stepper(pi=pi,
                                                logger=frankies_log,
                                                dir_pin=config.GPIO_STEPPER_0_DIR,
                                                on_pin=config.GPIO_STEPPER_0_ON,
                                                step_pin=config.GPIO_STEPPER_0_STEP,
                                                mode0_pin=config.GPIO_STEPPER_0_MODE0,
                                                mode1_pin=config.GPIO_STEPPER_0_MODE1,
                                                mode2_pin=config.GPIO_STEPPER_0_MODE2 )
    cleaner.cleanup_list.append(stepper_sprocket_01)


    camera = physical_control.Camera(pi=pi)


    last_warning = ""
    advancing = False

    if raw_input("Use Default(y/n? ") == 'y':
        speed = .001
        steps_per_frame = 291
        camera_pause = .5
        photo_count = 10
    else:
        speed = float(raw_input("Enter Speed in seconds (Lower = Faster)"))
        steps_per_frame = int(raw_input("Enter Steps Per Frame"))
        camera_pause = float(raw_input("Camera Pause Duration"))
        photo_count = int(raw_input("Number of Photos"))
        
    stepper_sprocket_01.max_speed = speed
    
    try:
        stepper_sprocket_01.turn_on()
        while True:
            
            for y in range(photo_count):
                
                camera.shutter()
                time.sleep(camera_pause)

                for x in range(steps_per_frame):
     
                    stepper_sprocket_01.one_step()
        
            camera.shutter()
            time.sleep(camera_pause)
        
            frankies_log.info("Series Complete - Returning to Start Position")
            for x in range(steps_per_frame):

                stepper_sprocket_01.one_step()
            raw_input("Press Key for Next Set")


    except KeyboardInterrupt:

        cleaner.clean_all()


if __name__ == "__main__":

    main()
