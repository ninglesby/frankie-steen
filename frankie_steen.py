import logging
import os
import time

import RPi.GPIO as GPIO
import Adafruit_ADS1x15

import config
import physical_control
import interface

def btn_power_short(logger, status):

    

    status.initial_engage()

    def null_report(logger):
        logger.info("Nothing assigned to power button short short_hold")


    return [null_report, logger]


def btn_power_med(logger, status, cleaner):


    status.warning()

    def shutdown_app(logger, cleaner):
        
        logger.info("Shutting down frankie_steen program")
        cleaner.cleanup()
        GPIO.cleanup()

    return [shutdown_app, logger, cleaner]


def btn_power_long(logger, status, cleaner):

    status.critical()

    def shutdown_total(logger, cleaner):

        logger.warning("Shutting down System")
        cleaner.cleanup()
        GPIO.cleanup()
        os.system("shutdown now -h")

    return [shutdown_total, logger, cleaner]

def btn_calibrate_short(logger, status, camera):

    status.initial_engage()

    def shutter_release(logger, status, camera):

        logger.info("Shutter Test Release")
        camera.shutter_release()
        status.snap()

    return [shutter_release, logger, status, camera]


def btn_calibrate_med(logger, status):

    status.warning()

    def reset_position_frame_count(logger, status):

        config.ROTATION = 0
        config.FRAME_COUNT = 0

        logger.info("Reset Rotation and Frame Count to 0")
        status.success()

    return [reset_position_frame_count, logger, status]


def btn_calibrate_long(logger, status):

    status.critical()

    def reset_total_frame_count(logger, status):

        physical_control.increment_frame_count(reset=True)
        logger.info("Reset Frame Count and Lifetime Frame Count to 0")
        status.success()

    return [reset_total_frame_count, logger, status]


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
    gpio_mode_status = interface.set_gpio_mode()

    if gpio_mode_status:

        frankies_log.warning(gpio_mode_status)

    # Initialize status object
    status = interface.Status(frankies_log)
    cleaner.cleanup_list.append(status)

    frankies_log.info("Initializing status object")
    status.nominal() # set status to nominal

    # Output logger info
    frankies_log.info("Starting up the frankie_steen")  

    camera = physical_control.Camera(pin=config.GPIO_CAMERA_SHUTTER)
    cleaner.cleanup_list.append(camera)

    # setup knobs for control
    knob_select = physical_control.Knob(   pin=config.ADC_KNOB_0, adc=adc, mode=config.ADC_KNOB_SELECT, selections=2 )
    cleaner.cleanup_list.append(knob_select)
    knob_spring = physical_control.Knob(   pin=config.ADC_KNOB_1, adc=adc, mode=config.ADC_KNOB_SWEEP, sweep_range=[-1,1] )
    cleaner.cleanup_list.append(knob_spring)
    knob_uptake = physical_control.Knob( pin=config.ADC_KNOB_2, adc=adc, mode=config.ADC_KNOB_SWEEP, sweep_range=[0,1])
    cleaner.cleanup_list.append(knob_uptake)

    toggle_run = physical_control.Toggle(  pin=config.GPIO_TOGGLE_RUN)
    cleaner.cleanup_list.append(toggle_run)

    toggle_uptake = physical_control.Toggle(   pin=config.GPIO_TOGGLE_UPTAKE)
    cleaner.cleanup_list.append(toggle_uptake)

    btn_power = physical_control.Button(   pin=config.GPIO_BTN_POWER,
                                    short_hold=btn_power_short,
                                    short_args=[frankies_log, status],
                                    med_hold=btn_power_med,
                                    med_args=[frankies_log, status, cleaner],
                                    long_hold=btn_power_long,
                                    long_args=[frankies_log, status, cleaner])
    cleaner.cleanup_list.append(btn_power)
    btn_power.start()

    btn_calibrate = physical_control.Button(   pin=config.GPIO_BTN_CALIBRATE,
                                        short_hold=btn_calibrate_short,
                                        short_args=[frankies_log, status, camera],
                                        med_hold=btn_calibrate_med,
                                        med_args=[frankies_log, status],
                                        long_hold=btn_power_long,
                                        long_args=[frankies_log, status])
    cleaner.cleanup_list.append(btn_calibrate)
    btn_calibrate.start()

    stepper_sprocket = physical_control.Stepper(    logger=frankies_log,
                                                    knob=knob_spring,
                                                    dir_pin=config.GPIO_STEPPER_0_DIR,
                                                    on_pin=config.GPIO_STEPPER_0_ON,
                                                    step_pin=config.GPIO_STEPPER_0_STEP,
                                                    mode0_pin=config.GPIO_STEPPER_0_MODE0,
                                                    mode1_pin=config.GPIO_STEPPER_0_MODE1,
                                                    mode2_pin=config.GPIO_STEPPER_0_MODE2 )
    cleaner.cleanup_list.append(stepper_sprocket)


    uptake_reel = physical_control.Stepper(     logger=frankies_log,
                                                knob=knob_uptake,
                                                dir_pin=config.GPIO_STEPPER_1_DIR,
                                                on_pin=config.GPIO_STEPPER_1_ON,
                                                step_pin=config.GPIO_STEPPER_1_STEP,
                                                mode="motor")
    cleaner.cleanup_list.append(uptake_reel)



    shutdown = False

    frankies_log.info("Starting Main Loop")

    current_speed_sprocket = 0
    current_knob_uptake = 0

    #mainloop
    try:
        current_mode = knob_select.get_selection()
        frankies_log.info("Current mode is %s" % str(current_mode))

        while not shutdown:

            
            # Manual Adjustment Mode
            if knob_select.get_selection() == config.SELECT_MANUAL_ADJUST:

                stepper_sprocket.mode = "motor"

                if current_mode != knob_select.get_selection():
                    frankies_log.info("Changed to Manual Adjustment Mode")
                    status.snap()
                    status.nominal()
                    current_mode = knob_select.get_selection()

                speed = knob_spring.get_value()

                if not speed == current_speed_sprocket:

                    current_speed_sprocket = speed

                    stepper_sprocket.set_speed(speed)

                    stepper_sprocket.motor()

                else:

                    time.sleep(.1)


                if stepper_sprocket.stop and stepper_sprocket.energized:

                    status.nominal()
                    frankies_log.debug("Stepper Power Down")
                    stepper_sprocket.turn_off()

                elif not stepper_sprocket.stop and not stepper_sprocket.energized:

                    status.operating()
                    frankies_log.debug("Stepper Power Up")
                    stepper_sprocket.turn_on()
                    stepper_sprocket.stepper()


            # Run Scan Mode
            if knob_select.get_selection() == config.SELECT_RUN:

                stepper_sprocket.mode = "stepper"

                if current_mode != knob_select.get_selection():
                    frankies_log.info("Changed to Run Mode")
                    status.snap()
                    status.nominal()
                    current_mode = knob_select.get_selection()


                if toggle_run.get_value():      

                    status.operating()

                    stepper_sprocket.advance_frame()

                    for step in stepper_sprocket.steps:
                        
                        if not current_knob_uptake == knob_uptake.get_value():
                            speed = knob_uptake.get_value()
                            uptake_reel.set_speed(speed)
                            uptake_reel.motor()

                        stepper_sprocket.stepper()

                    stepper_sprocket.steps = 0

                    camera.shutter_release()


                    frame_count, lifetime = physical_control.increment_frame_count()

                    frankies_log.info("Captured Frame: %s. Lifetime Capture: %s Frames" % (str(frame_count), lifetime_frame_count))

                    status.snap()  

                    #physical_control.capture_frame(frankies_log, status)


            if not current_knob_uptake == knob_uptake.get_value():
                speed = knob_uptake.get_value()
                uptake_reel.set_speed(speed)
                uptake_reel.motor()




            time.sleep(.5)

    except KeyboardInterrupt:

        shutdown = True

        frankies_log.info("Keyboard Interrupt, cleaning up threads and GPIO")

        cleaner.clean_all()

    return

if __name__ == "__main__":

    main()

