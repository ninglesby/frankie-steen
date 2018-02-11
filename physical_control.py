import threading
import time
import os
import pickle
import math

import RPi.GPIO as GPIO
import Adafruit_ADS1x15

import config


def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

class Stepper(threading.Thread):
    
    def __init__(   self, name="Stepper", dir_pin=0, on_pin=0,
                    step_pin=0, mode0_pin=0, mode1_pin=0, mode2_pin=0, knob=""):

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


        self.mode0_pin = mode0_pin
        self.mode1_pin = mode1_pin
        self.mode2_pin = mode2_pin
        self.speed = 0
        self.dir = 1
        self.stop = True
        self.steps = 0
        self.running_frame = False
        self.step_res_float = 1
        self.knob = knob

        threading.Thread.__init__(self, name=name)

    def run(self):

        self.change_step_res(config.STEPPER_RES)



        while not self._stopevent.isSet():

            GPIO.output(self.dir_pin, self.dir)

            if mode == "motor" and not self.stop:


                GPIO.output(self.step, GPIO.HIGH)
                GPIO.output(self.step, GPIO.LOW)

                time.sleep(self.speed_convert(self.speed))

            elif mode == "stepper" and self.steps:

                self.running_frame = True

                for x in range(self.steps):

                    GPIO.output(self.step, GPIO.HIGH)
                    GPIO.output(self.step, GPIO.LOW)

                self.steps = 0

                self.running_frame = False

    def set_speed(self, speed):

        if speed < 0:

            self.dir = 0

            speed = speed * -1

        else:

            self.dir = 1

        if knob:

            adjusted_threshold = abs((self.knob.sweep_range[1]-self.knob.sweep_range[0]) * config.ADC_KNOB_THRESHOLD)

            if speed < adjusted_threshold:

                speed = 0

            self.speed = translate(speed, self.knob.sweep_range[0], self.knob.sweep_range[1], config.STEPPER_MIN, config.STEPPER_MAX)

        else:

            self.speed = translate(speed, 0, 1, config.STEPPER_MIN, config.STEPPER_MAX)



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

    def cleanup(self):

        self._stopevent.set()

        GPIO.cleanup(dir_pin)
        GPIO.cleanup(on_pin)
        GPIO.cleanup(step_pin)
        
        if mode0_pin:
            GPIO.cleanup(mode0_pin)

        if mode1_pin:
            GPIO.cleanup(mode1_pin)

        if mode2_pin:
            GPIO.cleanup(mode2_pin)

        threading.Thread.join(self, None)


class UptakeReel(threading.Thread):

    def __init__(self, name=UptakeReel, knob="", dir_pin=0, on_pin=0, step_pin=0):

        self._stopevent = threading.Event( )

        self.knob = knob
        
        self.movement = Stepper( dir_pin=dir_pin, on_pin=on_pin, step_pin=step_pin)
        
        self.poll_time = .01
        threading.Thread.__init__(self, name=name)

    
    def run(self):

        while not self._stopevent.isSet():

            GPIO.wait_for_edge(self.knob.pin, GPIO.BOTH)

            while GPIO.output(self.knob.pin)

                speed = self.knob.get_value()
                movement.speed = speed

                time.sleep(self.poll_time)



    def join(self, timeout=None):
        """ Stop the thread and wait for it to end. """
        self.movement.cleanup()
        self._stopevent.set( )
        threading.Thread.join(self, timeout)

    def cleanup(self):

        self._stopevent.set()
        self.movement.cleanup()
        threading.Thread.join(self, None)

        




class Button(threading.Thread):

    def __init__(   self, name="Button",
                    pin=0, 
                    short_hold="", 
                    short_args=[],
                    med_hold="",
                    med_args=[],
                    long_hold="",
                    long_args=[]):

        self._stopevent = threading.Event( )
        self.pin = pin
        self.short_hold = short_hold
        self.short_args = short_args
        self.med_hold = med_hold
        self.med_args = med_args
        self.long_hold = long_hold
        self.long_args = long_args

        self.short_threshold = .25
        self.med_threshold = 2.0
        self.long_threshold = 4.0


        GPIO.setup(self.pin, GPIO.IN)

        threading.Thread.__init__(self, name=name)


    def run(self):

        while not self._stopevent.isSet():
            GPIO.wait_for_edge(self.pin)

            start_time = time.time()

            output = []

            while GPIO.input(self.pin):

                delta_time = time.time() - start_time

                if delta_time >= self.short_threshold and delta_time < self.med_threshold:

                    output = short_hold(*short_args)

                elif delta_time >= self.med_threshold and delta_time < self.long_threshold:

                    output = med_hold(*med_args)

                elif delta_time >= self.long_threshold:

                    output = med_hold(*long_args)

            if output:

                function = output.pop(0)

                function(*output)

    def join(self, timeout=None):

        self._stopevent.set( )
        threading.Thread.join(self, timeout)

    def cleanup(self):

        self._stopevent.set()
        GPIO.cleanup(self.pin)
        threading.Thread.join(self, None)





class Toggle()

    def __init__(self, pin=0):

        GPIO.setup(pin, GPIO.IN)

    def get_value(self):

        return GPIO.input(pin)

    def cleanup(self):

        GPIO.cleanup(pin)

class Knob():

    def __init__(   self, pin=0,
                    adc="",
                    mode=config.ADC_KNOB_SWEEP,
                    selections=0,
                    sweep_range=[0,1],
                    threshold=config.ADC_KNOB_THRESHOLD,
                    knob_hi=config.ADC_KNOB_HI,
                    knob_lo=config.ADC_KNOB_LO):
        
        self.pin = pin
        self.adc = adc
        self.mode = mode
        self.selections = selections
        self.sweep_range = sweep_range
        self.threshold = threshold
        self.knob_hi = knob_hi
        self.knob_lo = knob_lo
        self.gain = config.ADC_GAIN

    def get_selection(self):
        
        value = self.adc.read_adc(self.pin, gain=self.gain)

        full_range = self.knob_hi - self.knob_lo

        increments = full_range / self.selections

        for x in range(self.selections):

            if value >= (x*self.knob_lo) and value < ((x+1)*self.knob_lo):

                return x

    def get_value(self):

        value = self.adc.read_adc(self.pin, gain=self.gain)

        mapped_value = translate(value, self.knob_lo, self.knob_hi, self.sweep_range[0],self.sweep_range[1])

    def cleanup(self):

        return True






class Camera():

    def __init__(self, pin=0):

        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)

    def shutter_release(self):

        GPIO.output(self.pin, GPIO_HIGH)
        time.sleep(.1)
        GPIO.output(self.pin, GPIO_LOW)

    def cleanup(self)

        GPIO.cleanup(self.pin)



def increment_frame_count(reset=False):

    odometer = os.path.join(os.path.dirname(config.LOG_LOCATION), "odometer")

    if reset:
        config.FRAME_COUNT = 0
    else:
        config.FRAME_COUNT += 1

    with open(odometer, "r+") as f:
        lifetime_frame_count = f.read().replace(" ", "")

        string_length = len(lifetime_frame_count)

        if reset:

            lifetime_frame_count = str(0) + " " * string_length

        else:

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

    #odometer = os.path.join(os.path.dirname(config.LOG_LOCATION) + "odometer")

    frame_count, lifetime = increment_frame_count()

    logger.info("Captured Frame: %s. Lifetime Capture: %s Frames" % (str(frame_count), lifetime_frame_count))

    status.snap()




