import threading
import time
import os
import pickle
import math
from collections import OrderedDict

#import RPi.GPIO as GPIO
import pigpio
pi = pigpio.pi()

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



class Stepper():
    
    def __init__(   self, logger="",
                    dir_pin=1,
                    on_pin=0,
                    step_pin=0,
                    mode0_pin=0,
                    mode1_pin=0,
                    mode2_pin=0,
                    mode="stepper",
                    default_dir=1,
                    frequencies=config.GPIO_FREQUENCIES,
                    floats=config.STEPPER_FLOATS):


        self.dir_pin = dir_pin
        self.default_dir = default_dir
        self.on_pin = on_pin
        self.step_pin = step_pin
        self.mode0_pin = mode0_pin
        self.mode1_pin = mode1_pin
        self.mode2_pin = mode2_pin
        self.speed = 0
        self.dir = 1
        self.energized = 1
        self.stop = False
        self.steps = 0
        self.step_res_float = 1.0
        self.mode = mode
        self.change_step_res(config.STEPPER_RES)
        self.logger = logger
        self.rewind = False
        self.max_speed = config.STEPPER_MAX
        self.speeds, self.speed_params = self.generate_speeds(frequencies, floats)
        self.threshold = config.ADC_KNOB_THRESHOLD
        self.current_mode = ""
        


    def motor(self):

        if self.current_mode != "MOTOR":

            self.current_mode = "MOTOR"
            self.logger.debug("Motor mode enabled")

        if not self.stop:
            self.turn_on()
            pi.set_PWM_dutycycle(self.step_pin, 150)

        else:
            self.turn_off()
            pi.set_PWM_dutycycle(self.step_pin, 0)

    def one_step(self):

        starting = pi.read(self.step_pin)

        pi.write(self.step_pin, not starting)

        time.sleep(self.max_speed)

        pi.write(self.step_pin, starting)
            

    def stepper(self):

        if self.current_mode != "STEPPER":

            self.current_mode = "STEPPER"
            self.logger.debug("Stepper mode enabled.")

        if not self.stop and self.steps:

            self.turn_on()
            
            if self.rewind:

                pi.write(self.dir_pin, not self.default_dir)

            else:

                pi.write(self.dir_pin, self.default_dir)


            for step in range(self.steps):

                if not self.stop:

                    self.one_step()


    def turn_on(self):

        if not self.energized:
            self.logger.debug("Stepper powered on")
        pi.write(self.on_pin, 1)
        self.energized = 1

    def turn_off(self):

        if self.energized:
            self.logger.debug("Stepper powered off")
        pi.write(self.on_pin, 0)
        self.energized = 0

    def set_speed(self, speed):

        if speed > 0 + self.threshold:
            
            self.turn_on()
            self.stop = False
            pi.write(self.dir_pin, 1)

        elif speed < 0 - self.threshold:

            self.turn_on()
            self.stop = False
            pi.write(self.dir_pin, 0) 
            speed = -1.0 * speed

        else:

            self.stop = True
            self.turn_off()

        speed_index = int(round(translate(speed, 0.0, 1.0, 0, len(self.speeds)-1)))

        frequency = self.speed_params[self.speeds[speed_index]][0]

        step_res = self.speed_params[self.speeds[speed_index]][1]




        pi.set_PWM_frequency(self.step_pin, frequency)

        self.change_step_res(step_res)




    def advance_frame(self):


        steps_per_degree = ( config.STEPPER_TOTAL_STEPS / self.step_res_float ) / 360.0

        self.steps = int(config.STEPPER_FRAME_DEGREE * steps_per_degree)




        

    def change_step_res(self, step_res):


        config.STEPPER_RES = step_res

        if step_res == "1" or step_res == 1.0:

            self.step_res_float = 1.0
            pi.write(self.mode0_pin, 0)
            pi.write(self.mode1_pin, 0)
            pi.write(self.mode2_pin, 0)

        elif step_res == "1/2" or step_res == .5:

            self.step_res_float = 0.5
            pi.write(self.mode0_pin, 1)
            pi.write(self.mode1_pin, 0)
            pi.write(self.mode2_pin, 0)

        elif step_res == "1/4" or step_res == .25:

            self.step_res_float = 0.25
            pi.write(self.mode0_pin, 0)
            pi.write(self.mode1_pin, 1)
            pi.write(self.mode2_pin, 0)

        elif step_res == "1/8" or step_res == .125:

            self.step_res_float = 0.125
            pi.write(self.mode0_pin, 1)
            pi.write(self.mode1_pin, 1)
            pi.write(self.mode2_pin, 0)

        elif step_res == "1/16" or step_res == .0625:

            self.step_res_float = 0.0625
            pi.write(self.mode0_pin, 0)
            pi.write(self.mode1_pin, 0)
            pi.write(self.mode2_pin, 1)

        elif step_res == "1/32" or step_res == .03125:

            self.step_res_float = 0.03125
            pi.write(self.mode0_pin, 1)
            pi.write(self.mode1_pin, 0)
            pi.write(self.mode2_pin, 1)

    def cleanup(self):


        pi.cleanup(self.dir_pin)
        pi.cleanup(self.on_pin)
        pi.cleanup(self.step_pin)
        
        if self.mode0_pin:
            pi.cleanup(self.mode0_pin)

        if self.mode1_pin:
            pi.cleanup(self.mode1_pin)

        if self.mode2_pin:
            pi.cleanup(self.mode2_pin)

    def generate_speeds(self, rows, columns):


        self.logger.info("Generating Speeds")

        values = {}
        indices = []


        for row in rows:

            for column in columns:

                index = row*column
                indices.append(index)

                try:

                    if row > values[index][0]:

                        values[index] = [row, column]
                
                except KeyError:

                    values[index] = [row, column]


        indices = list(set(indices))
        indices.sort()


        return indices, values





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

        selection = int(round(translate(value, self.knob_hi, self.knob_lo, 1, self.selections)))

        return selection


    def get_value(self):

        value = self.adc.read_adc(self.pin, gain=self.gain)

        mapped_value = translate(value, self.knob_lo, self.knob_hi, self.sweep_range[0],self.sweep_range[1])

        return mapped_value

    def cleanup(self):

        return True




def increment_frame_count(reset=False):

    odometer = os.path.join(os.path.dirname(config.LOG_LOCATION), "odometer")

    if reset:
        config.FRAME_COUNT = 0
    else:
        config.FRAME_COUNT += 1

    if not os.path.exists(odometer):

        with open(odometer, "wb") as f:

            f.write(str(0))

            
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