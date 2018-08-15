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
    adc = Adafruit_ADS1x15.ADS1115()

    display = interface.Display()


    # Create an instance of the logger
    frankies_log = interface.FrankiesLog().logger

    status = interface.Status(logger=frankies_log, display=display)

    
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

    cleaner.cleanup_list.append(display)


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

    stepper_sprocket_02 = physical_control.Stepper(pi=pi,
                                                logger=frankies_log,
                                                dir_pin=config.GPIO_STEPPER_2_DIR,
                                                on_pin=config.GPIO_STEPPER_2_ON,
                                                step_pin=config.GPIO_STEPPER_2_STEP,
                                                mode0_pin=config.GPIO_STEPPER_2_MODE0,
                                                mode1_pin=config.GPIO_STEPPER_2_MODE1,
                                                mode2_pin=config.GPIO_STEPPER_2_MODE2 )
    cleaner.cleanup_list.append(stepper_sprocket_02)

    motor_takeup = physical_control.Stepper(    pi=pi,
                                                logger=frankies_log,
                                                dir_pin=config.GPIO_MOTOR_1_DIR,
                                                step_pin=config.GPIO_STEPPER_1_ON,
                                                )
    cleaner.cleanup_list.append(motor_takeup)

    knob_spring = interface.Knob(   pin=config.ADC_KNOB_1, adc=adc, mode=config.ADC_KNOB_SWEEP, sweep_range=[-1,1] )
    cleaner.cleanup_list.append(knob_spring)

    knob_select = interface.Knob(   pin=config.ADC_KNOB_0, adc=adc, mode=config.ADC_KNOB_SELECT, selections=2 )
    cleaner.cleanup_list.append(knob_select)

    knob_motor = interface.Knob(    pin=config.ADC_KNOB_2,
                                    adc=adc,
                                    mode=config.ADC_KNOB_SWEEP,
                                    knob_hi=24000,
                                    knob_lo=13000,
                                    sweep_range=[0.0,1.0],
                                    hard_limit=True )
    cleaner.cleanup_list.append(knob_motor)
    
    blue_light = interface.Light(   pi=pi,
                                    logger=frankies_log,
                                    light_pin=config.GPIO_STATUS_BLUE,
                                    )

    btn_calibrate_cbs = [   
                            {   "function":btn_calibrate_cb0,
                                "time":0.0,
                                "args":[pi],
                                "notify_function":btn_calibrate_n0,
                                "notify_args":[status]},
                            
                            {   "function":btn_calibrate_cb1,
                                "time":2.0,
                                "args":[],
                                "notify_function":btn_calibrate_n1,
                                "notify_args":[status]}
                        ]

    btn_calibrate = interface.Switch(   name="Calibrate Button",
                                        logger=frankies_log,
                                        pi=pi,
                                        switch_pin=config.GPIO_BTN_CALIBRATE,
                                        callbacks=btn_calibrate_cbs,
                                        mode="BUTTON",
                                        PULL_UP_DOWN="UP")
    cleaner.cleanup_list.append(btn_calibrate)

    camera = physical_control.Camera(pi=pi)


    last_warning = ""
    advancing = False


    try:

        while True:

            motor_dutycycle = helpers.translate(    knob_motor.get_value(),
                                                    knob_motor.sweep_range[0],
                                                    knob_motor.sweep_range[1],
                                                    0,
                                                    255,
                                                    "LINEAR")
            #################THIS IS FOR YOU PAT!!!###############################
            motor_dutycycle = 100 - motor_dutycycle################################################MOTOR SPEED

            if motor_dutycycle < 0:
                motor_dutycycle = 0

            motor_takeup.dc_motor(dutycycle=motor_dutycycle)
            #pi.write(config.GPIO_STEPPER_1_ON, 0)                                                 

            if knob_select.get_selection() == 1:



                if not stepper_sprocket_01.steps and not stepper_sprocket_02.steps and not advancing:
                    #display.message(title="RUN MODE")

                    step_index = int( helpers.translate(    knob_spring.get_value(),
                                                            knob_spring.sweep_range[0],
                                                            knob_spring.sweep_range[1],
                                                            0,
                                                            len(config.STEPPER_FLOATS),
                                                            "LINEAR" )
                                                        )

                    stepper_sprocket_01.turn_on()
                    stepper_sprocket_02.turn_on()
                    stepper_sprocket_01.change_step_res(config.STEPPER_FLOATS[step_index])
                    stepper_sprocket_02.change_step_res(config.STEPPER_FLOATS[step_index])
                    stepper_sprocket_01.advance_frame()
                    stepper_sprocket_02.advance_frame()

                    advancing = True

                elif not stepper_sprocket_01.steps and not stepper_sprocket_02.steps and advancing:

                    advancing = False

                    motor_takeup.dc_motor(dutycycle=0)
                    pi.write(config.GPIO_STEPPER_1_ON, 0)
                    frame_count, lifetime_frame_count = helpers.increment_frame_count()



                    camera.shutter()


                    frankies_log.info("Captured Frame: %s. Lifetime Capture: %s Frames" % (str(frame_count), lifetime_frame_count))
                    display.message(text=["Captured Frame", str(frame_count), "Lifetime Capture", str(lifetime_frame_count), "Frames"])

                    time.sleep(.500)



                else:

                    t1 = Thread(target=stepper_sprocket_01.one_step)
                    t2 = Thread(target=stepper_sprocket_02.one_step)

                    t1.start()
                    t2.start()

                    stepper_sprocket_01.steps -= 1
                    stepper_sprocket_02.steps -= 1

                    t1.join()
                    t2.join()



            elif knob_select.get_selection() == 2:
            
                stepper_sprocket_01.set_speed(knob_spring.get_value())
                stepper_sprocket_02.set_speed(knob_spring.get_value())
                
                stepper_sprocket_01.motor()
                stepper_sprocket_02.motor()


            else:

                if last_warning != "Invalid Selection":

                    last_warning = "Invalid Selection"
                    frankies_log.warning("%s is an invalid selection" % str(knob_select.get_value()))

            btn_calibrate.check_button()
            #status.update_display()
            if not advancing:
                time.sleep(.02)

            #blue_light.set_light(mode="CONSTANT")

    except KeyboardInterrupt:

        cleaner.clean_all()


if __name__ == "__main__":

    main()
