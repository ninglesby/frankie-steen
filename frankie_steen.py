import logging

import RPi.GPIO as GPIO

import config
import physical_control
import interface



def main():

    # Create an instance of the logger
    frankies_log = interface.FrankiesLog().logger

    #set gpio mode status, doesn't return anything if it was successful 
    #returns message if there is an error.
    gpio_mode_status = interface.set_gpio_mode():

    if gpio_mode_status:

        frankies_log.warning(gpio_mode_status)

    # Initialize status object
    status = interface.Status(frankies_log)
    frankies_log.info("Initializing status object")
    status.nominal() # set status to nominal

    # Output logger info
    frankies_log.info("Starting up the frankie_steen")  

    # setup knobs for control
    knob_select = interface.KnobSelect(pin=config.ADC_KNOB_0)
    knob_spring = interface.KnobSweep(pin=config.ADC_KNOB_1)

    toggle_run = interface.Toggle(pin=config.GPIO_TOGGLE_RUN)
    toggle_uptake = interface.Toggle(pin=config.GPIO_TOGGLE_UPTAKE)

    btn_power = interface.Button(pin=config.GPIO_BTN_POWER)
    btn_calibrate = interface.Button(pin=config.GPIO_BTN_CALIBRATE)

    stepper_sprocket = physical_control.Stepper(    dir_pin=config.GPIO_STEPPER_0_DIR,
                                                    on_pin=config.GPIO_STEPPER_0_ON,
                                                    step_pin=config.GPIO_STEPPER_0_STEP,
                                                    mode0_pin=config.GPIO_STEPPER_0_MODE0,
                                                    mode1_pin=config.GPIO_STEPPER_0_MODE1,
                                                    mode2_pin=config.GPIO_STEPPER_0_MODE2 )

    camera = physical_control.Camera(pin=config.GPIO_CAMERA_SHUTTER)




    shutdown = False


    #mainloop
    try:
        current_mode = knob_select.get_mode()
        while not shutdown:

            # Manual Adjustment Mode
            if knob_select.get_mode() == 0:

                if current_mode != knob_select.get_mode:
                    frankies_log.info("Changed to Manual Adjustment Mode")
                    status.nominal()

                speed = knob_spring.get_value()
                direction = knob_spring.get_direction()

                stepper_sprocket.speed = speed
                stepper_sprocket.direction = direction

                if not speed and stepper_sprocket.energized:

                    status.nominal()
                    frankies_log.debug("Stepper Power Down")
                    stepper_sprocket.turn_off()

                elif speed and not stepper_sprocket.energized:

                    status.operating()
                    frankies_log.debug("Stepper Power Up")
                    stepper_sprocket.turn_on()


            # Run Scan Mode
            if knob_select.get_mode() == 1:

                if current_mode != knob_select.get_mode:
                    frankies_log.info("Changed to Run Mode")
                    status.nominal()


                if toggle_run.get_value():      

                    status.operating()

                    physical_control.capture_frame(frankies_log, status)


            time.sleep(.01)

    except KeyboardInterrupt:

        frankies_log.info("Keyboard Interrupt, cleaning up threads and GPIO")

        status.cleanup()
        physical_control.cleanup()

