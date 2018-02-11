import threading
import time
import os
import pickle
import math

import RPi.GPIO as GPIO
import Adafruit_ADS1x15




class Stepper(threading.Thread):
    
    def __init__(self, name="Stepper", dir_pin=0, on_pin=0, step_pin=0, mode0_pin=0, mode1_pin=0, mode2_pin=0):

        self._stopevent = threading.Event( )
        GPIO.setup(dir_pin, GPIO.OUT)
        GPIO.setup(on_pin, GPIO.OUT)
        GPIO.setup(step_pin, GPIO.OUT)
        
        if mode0_pin:
            GPIO.setup(mode0_pin, GPIO.OUT)

        if mode1_pin:
            GPIO.setup(mode1_pin, GPIO.OUT)

        if mode2_pin:
            GPIO.setup(mode2_pin, GPIO.OUT)

        threading.Thread.__init__(self, name=name)

        self.mode0_pin = mode0_pin
        self.mode1_pin = mode1_pin
        self.mode2_pin = mode2_pin
        self.speed = 0
        self.dir = 1
        self.stop = True
        self.steps = 0
        self.running_frame = False
        self.step_res_float = 1


    def run(self):

        self.change_step_res(config.STEPPER_RES)



        while not self._stopevent.isSet():

            GPIO.output(self.dir_pin, self.dir)

            if mode == "motor" and not self.stop:


                GPIO.output(self.step, GPIO.HIGH)
                GPIO.output(self.step, GPIO.LOW)

                time.sleep(self.speed)

            elif mode == "stepper" and self.steps:

                self.running_frame = True

                for x in range(self.steps):

                    GPIO.output(self.step, GPIO.HIGH)
                    GPIO.output(self.step, GPIO.LOW)

                self.steps = 0

                self.running_frame = False

    def advance_frame(self):


        steps_per_degree = ( config.STEPPER_TOTAL_STEPS / self.step_res_float ) / 360.0

        self.steps = math.round(config.STEPPER_FRAME_DEGREE * steps_per_degree)


        

    def change_step_res(self, step_res):

        config.STEPPER_RES = step_res

        if step_res == "1":

            self.step_res_float = 1.0
            GPIO.output(self.MODE0_pin, 0)
            GPIO.output(self.MODE1_pin, 0)
            GPIO.output(self.MODE2_pin, 0)

        elif step_res == "1/2":

            self.step_res_float = 0.5
            GPIO.output(self.MODE0_pin, 0)
            GPIO.output(self.MODE1_pin, 0)
            GPIO.output(self.MODE2_pin, 0)

        elif step_res == "1/4":

            self.step_res_float = 0.25
            GPIO.output(self.MODE0_pin, 0)
            GPIO.output(self.MODE1_pin, 0)
            GPIO.output(self.MODE2_pin, 0)

        elif step_res == "1/8":

            self.step_res_float = 0.125
            GPIO.output(self.MODE0_pin, 0)
            GPIO.output(self.MODE1_pin, 0)
            GPIO.output(self.MODE2_pin, 0)

        elif step_res == "1/16":

            self.step_res_float = 0.0625
            GPIO.output(self.MODE0_pin, 0)
            GPIO.output(self.MODE1_pin, 0)
            GPIO.output(self.MODE2_pin, 0)

        elif step_res == "1/16":

            self.step_res_float = 0.03125
            GPIO.output(self.MODE0_pin, 0)
            GPIO.output(self.MODE1_pin, 0)
            GPIO.output(self.MODE2_pin, 0)

    def join(self, timeout=None):
        """ Stop the thread and wait for it to end. """
        self._stopevent.set( )
        threading.Thread.join(self, timeout)


class UptakeReel(threading.Thread):

    def __init__(self, name=UptakeReel):

        self._stopevent = threading.Event( )

        self.knob = KnobSweep(mode="LO_HI")
        
        self.movement = Stepper(    dir_pin=config.GPIO_STEPPER_1_DIR,
                                    on_pin=config.GPIO_STEPPER_1_ON,
                                    step_pin=config.GPIO_STEPPER_1_STEP,)
        
        self.poll_time = .01
        threading.Thread.__init__(self, name=name)

    
    def run(self):

        while not self._stopevent.isSet():

            GPIO.wait_for_edge(config.GPIO_TOGGLE_UPTAKE, GPIO.BOTH)

            while GPIO.output(config.GPIO_TOGGLE_UPTAKE)

                speed = self.knob.get_value()
                movement.speed = speed

                time.sleep(self.poll_time)



    def join(self, timeout=None):
        """ Stop the thread and wait for it to end. """
        self._stopevent.set( )
        threading.Thread.join(self, timeout)

        




class Button(threading.Thread):

    def __init__ 

class Toggle

class KnobSelect

class KnobSweep



class Camera():

    def __init__(self, pin=0):

        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)

    def shutter_release(self):

        GPIO.output(self.pin, GPIO_HIGH)
        time.sleep(.1)
        GPIO.output(self.pin, GPIO_LOW)



def increment_frame_count(odometer):

    config.FRAME_COUNT += 1

    with open(odometer, "r+") as f:
        lifetime_frame_count = f.read()

        lifetime_frame_count = str(int(lifetime_frame_count)+1)

        f.seek(0)
        f.write(lifetime_frame_count)

    return config.FRAME_COUNT, lifetime_frame_count


def capture_frame(logger, status, stepper, camera):

    
    stepper.advance_frame()

    time.sleep(.01)

    while stepper.steps:

        time.sleep(.01)

    camera.shutter_release()

    odometer = os.path.join(os.path.dirname(config.LOG_LOCATION) + "odometer")

    frame_count, lifetime = increment_frame_count(odometer)

    logger.info("Captured Frame: %s. Lifetime Capture: %s Frames" % (str(frame_count), lifetime_frame_count))

    status.snap()




