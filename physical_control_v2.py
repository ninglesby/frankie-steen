import threading
import time
import os
import pickle
import math
from collections import OrderedDict

#import RPi.GPIO as GPIO
import pigpio

import Adafruit_ADS1x15

import config
import helpers





class Stepper():
    
    def __init__(   self, logger="",
                    pi="",
                    dir_pin=1,
                    on_pin=0,
                    step_pin=0,
                    mode0_pin=0,
                    mode1_pin=0,
                    mode2_pin=0,
                    mode="stepper",
                    default_dir=1,
                    frequencies=config.GPIO_FREQUENCIES,
                    floats=config.STEPPER_FLOATS,
                    translate_mode="LOG"):

        self.pi = pi
        self.dir_pin = dir_pin
        self.default_dir = default_dir
        self.on_pin = on_pin
        self.step_pin = step_pin
        self.mode0_pin = mode0_pin
        self.mode1_pin = mode1_pin
        self.mode2_pin = mode2_pin

        pi.set_mode(self.dir_pin, pigpio.OUTPUT)
        pi.set_mode(self.on_pin, pigpio.OUTPUT)
        pi.set_mode(self.step_pin, pigpio.OUTPUT)

        if self.mode0_pin:
            pi.set_mode(self.mode0_pin, pigpio.OUTPUT)

        if self.mode1_pin:
            pi.set_mode(self.mode1_pin, pigpio.OUTPUT)

        if self.mode2_pin:
            pi.set_mode(self.mode2_pin, pigpio.OUTPUT)

        self.speed = 0
        self.dir = 1
        self.energized = 1
        self.stop = False
        self.steps = 0
        self.step_res_float = 1.0
        self.mode = mode
        self.logger = logger
        self. current_step_res = None
        self.change_step_res(config.STEPPER_RES)
        self.rewind = False
        self.max_speed = config.STEPPER_MAX
        self.speeds, self.speed_params = self.generate_speeds(frequencies, floats)
        self.threshold = config.ADC_KNOB_THRESHOLD
        self.current_mode = ""
        self.frequency = 800
        self.translate_mode = translate_mode
        


    def motor(self):

        if self.current_mode != "MOTOR":

            self.current_mode = "MOTOR"

            if self.logger:
                self.logger.debug("Motor mode enabled")
            else:
                print "Motor mode enabled"

        if not self.stop:
            self.turn_on()
            self.pi.hardware_PWM(self.step_pin, self.frequency, 250000)

        else:
            self.turn_off()
            self.pi.hardware_PWM(self.step_pin, self.frequency, 250000)

    def one_step(self):

        starting = self.pi.read(self.step_pin)

        self.pi.write(self.step_pin, not starting)

        time.sleep(self.max_speed)

        self.pi.write(self.step_pin, starting)
            

    def stepper(self):

        if self.current_mode != "STEPPER":

            self.stop = False

            self.current_mode = "STEPPER"

            if self.logger:
                self.logger.debug("Stepper mode enabled.")
            else:
                print "Stepper mode enabled."

        if not self.stop and self.steps:

            self.turn_on()
            
            if self.rewind:

                self.pi.write(self.dir_pin, not self.default_dir)

            else:

                self.pi.write(self.dir_pin, self.default_dir)


            for step in range(self.steps):

                if not self.stop:

                    self.one_step()


    def turn_on(self):

        if not self.energized:
            
            if self.logger:
                self.logger.debug("Stepper powered on")
            else:
                print "Stepper power on"

        self.pi.write(self.on_pin, 1)
        self.energized = 1

    def turn_off(self):

        if self.energized:

            if self.logger:
                self.logger.debug("Stepper powered off")
            else:
                print "Stepper powered off"

        self.pi.write(self.on_pin, 0)

        self.energized = 0

    def set_speed(self, speed):

        if speed > 0 + self.threshold:
            
            self.turn_on()
            self.stop = False
            self.pi.write(self.dir_pin, 1)

        elif speed < 0 - self.threshold:

            self.turn_on()
            self.stop = False
            self.pi.write(self.dir_pin, 0) 
            speed = -1.0 * speed

        else:

            self.stop = True
            self.turn_off()

        speed_index = int( round( helpers.translate( speed, 0.0, 1.0, 0, len(self.speeds)-1, self.translate_mode ) ) )

        frequency = self.speed_params[self.speeds[speed_index]][0]

        step_res = self.speed_params[self.speeds[speed_index]][1]


        if not frequency == self.frequency:

            self.logger.debug("Frequency changed to %s" % str(frequency))

            self.frequency = frequency
            self.pi.set_PWM_frequency(self.step_pin, frequency)

        self.change_step_res(step_res)




    def advance_frame(self):


        steps_per_degree = ( config.STEPPER_TOTAL_STEPS / self.step_res_float ) / 360.0

        self.steps = int(config.STEPPER_FRAME_DEGREE * steps_per_degree)

        

    def change_step_res(self, step_res):


        if step_res == config.STEPPER_RES:

            pass

        else:

            config.STEPPER_RES = step_res



            if step_res == "1" or step_res == 1.0: 

                self.logger.debug("Changed Step Res to 1. 0 - 0 - 0")

                self.step_res_float = 1.0
                self.pi.write(self.mode0_pin, 0)
                self.pi.write(self.mode1_pin, 0)
                self.pi.write(self.mode2_pin, 0)

            elif step_res == "1/2" or step_res == .5:

                self.logger.debug("Changed Step Res to 1/2. 1 - 0 - 0")

                self.step_res_float = 0.5
                self.pi.write(self.mode0_pin, 1)
                self.pi.write(self.mode1_pin, 0)
                self.pi.write(self.mode2_pin, 0)

            elif step_res == "1/4" or step_res == .25:

                self.logger.debug("Changed Step Res to 1/4. 0 - 1 - 0")

                self.step_res_float = 0.25
                self.pi.write(self.mode0_pin, 0)
                self.pi.write(self.mode1_pin, 1)
                self.pi.write(self.mode2_pin, 0)

            elif step_res == "1/8" or step_res == .125:

                self.logger.debug("Changed Step Res to 1/8. 1 - 1 - 0")

                self.step_res_float = 0.125
                self.pi.write(self.mode0_pin, 1)
                self.pi.write(self.mode1_pin, 1)
                self.pi.write(self.mode2_pin, 0)

            elif step_res == "1/16" or step_res == .0625:

                self.logger.debug("Changed Step Res to 1/16. 0 - 0 - 1")

                self.step_res_float = 0.0625
                self.pi.write(self.mode0_pin, 0)
                self.pi.write(self.mode1_pin, 0)
                self.pi.write(self.mode2_pin, 1)

            elif step_res == "1/32" or step_res == .03125:

                self.logger.debug("Changed Step Res to 1/32. 1 - 0 - 1")

                self.step_res_float = 0.03125
                self.pi.write(self.mode0_pin, 1)
                self.pi.write(self.mode1_pin, 0)
                self.pi.write(self.mode2_pin, 1)

    def cleanup(self):


        self.pi.write(self.dir_pin, 0)
        self.pi.write(self.on_pin, 0)
        self.pi.write(self.step_pin, 0)
        
        if self.mode0_pin:
            self.pi.write(self.mode0_pin, 0)

        if self.mode1_pin:
            self.pi.write(self.mode1_pin, 0)

        if self.mode2_pin:
            self.pi.write(self.mode2_pin, 0)

    def generate_speeds(self, rows, columns):

        if self.logger:
            self.logger.info("Generating Speeds")
        else:
            print "Generating Speeds"

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

    





class PhotoGate():

    def __init__():

        return
    def function(self):

        return




