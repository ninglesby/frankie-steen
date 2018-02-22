import logging
import threading
import time

import RPi.GPIO as GPIO
import pigpio

import config
import helpers
import interface_v2 as interface


#A logging class for better debugging over just printing to the console
class FrankiesLog:

    def __init__(self):

        # create logger
        self.logger = logging.getLogger(config.LOG_NAME)
        self.logger.setLevel(config.LOG_VERBOSITY)

        # create console handler and set level to debug
        self.ch = logging.StreamHandler()
        self.ch.setLevel(config.LOG_SHELL_VERBOSITY)

        # create file handler and set level to debug
        self.fh = logging.FileHandler(config.LOG_LOCATION)
        self.fh.setLevel(config.LOG_VERBOSITY)

        # create formatter
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to ch and fh
        self.ch.setFormatter(self.formatter)
        self.fh.setFormatter(self.formatter)

        # add ch and fh to logger
        self.logger.addHandler(self.ch)
        self.logger.addHandler(self.fh)


#A class for setting up an individual light

class Light():

    def __init__(self, pi="", logger=None, light_pin=0, mode="CONSTANT", brightness=255, blink_speed=0):

        self.light_pin = light_pin
        self.mode = mode
        self.brightness = brightness
        self.blink_speed = blink_speed
        self.frequency  = 200
        self.logger = logger
        self.pi = pi

    def set_light(self, mode=None, brightness=None, blink_speed=None):

        if mode:
            self.mode = mode

        if brightness:
            self.brightness = brightness

        if blink_speed:
            self.blink_speed = blink_speed


        if self.mode == "CONSTANT":

            self.pi.write(self.light_pin, 1)
            self.pi.set_PWM_frequency(self.light_pin, 200)
            self.pi.set_PWM_dutycycle(self.light_pin, self.brightness)

        elif self.mode == "BLINK":

            self.pi.write(self.light_pin, 1)

            self.set_speed(self.blink_speed)

            self.pi.set_PWM_dutycycle(self.light_pin, 150)

            return ""

        else:

            return "Invalid mode"

    def set_speed(self, blink_speed=None):

        speeds = [  10,
                    20,
                    40,
                    50,
                    80,
                    100,
                    160,
                    200,
                    250]

        if blink_speed:
            self.blink_speed = blink_speed

        self.pi.set_PWM_frequency(self.light_pin, speeds[self.blink_speed])




# Controls for RGB light on a raspberry pi
class RGBLightController():
    
    def __init__(self, pi="", logger="", red=27, green=17, blue=26, freq=50):

        pi.set_mode(red, pigpio.OUTPUT)
        pi.set_mode(green, pigpio.OUTPUT)
        pi.set_mode(blue, pigpio.OUTPUT)
        self.red = red
        self.green = green
        self.blue = blue

        
        self.logger = logger

    def hsl(self, h, s, l):
        saturation = s/100.0
        luminance = l/100.0
        r,g,b = self.hueCycle(h)
        average = (r+g+b)/3.0

        red = (r*saturation + average*(1.0-saturation))*luminance
        green = (g*saturation + average*(1.0-saturation))*luminance
        blue = (b*saturation + average*(1.0-saturation))*luminance
        rgb = {"r":red, "g":green, "b":blue}
        
        for c in rgb:
            if rgb[c] > 100.0:
                rgb[c] = 100.0
            elif rgb[c] < 0.0:
                rgb[c] = 0.0
        
        self.pi.set_PWM_dutycycle(self.red, rgb["r"])
        self.pi.set_PWM_dutycycle(self.green, rgb["g"])
        self.pi.set_PWM_dutycycle(self.blue, rgb["b"])

    def rgb(self, r, g, b):

        self.pi.set_PWM_dutycycle(self.red, rgb["r"])
        self.pi.set_PWM_dutycycle(self.green, rgb["g"])
        self.pi.set_PWM_dutycycle(self.blue, rgb["b"])

        
    def hueCycle(self, percent):

        if percent <= 33.3:
            blue =  0
            red = (100-percent*3)
            green = (percent*3)
            
        elif percent > 33.3 and percent < 66.6:
            red = 0
            green = (100-(percent - 33.3)*3)
            blue = ((percent - 33.3)*3)
            
        elif percent >= 66.6:
            
            green = 0
            blue = (100 - (percent - 66.6)*3)
            red = ((percent - 66.6)*3)
            
        return red, green, blue

    def cleanup(self):

        self.pi.write(self.red,0)
        self.pi.write(self.green,0)
        self.pi.write(self.blue,0)

# class to handle status operations
class Status():

    def __init__(self, logger=""):

        #initialize lights on the Raspberry Pi
        self.lite = RGBLightController( logger=logger,
                                        red=config.GPIO_STATUS_RED,
                                        green=config.GPIO_STATUS_GREEN,
                                        blue=config.GPIO_STATUS_BLUE)

        #initalize light thread
        self.lightthread = LightThread( logger=logger, lite=self.lite)
        #self.lightthread.start()

        self.logger = logger

        self.current_status = ""

    def nominal(self):

        if self.current_status != "nominal":
            self.lightthread.color = [0,100,0] # green
            self.lightthread.mode = 2 # constant
            self.current_status = "nominal"
            self.logger.info("Status changed to nominal")

    def warning(self):
        
        if self.current_status != "warning":
            self.lightthread.color = [75, 75, 0] # yellow
            self.lightthread.mode = 7 # medium pulse
            self.current_status = "warning"
            self.logger.warning("Status changed to warning")

    def critical(self):
        
        if self.current_status != "critical":
            self.lightthread.color = [100, 0, 0] # red
            self.lightthread.mode = 4 # medium blink
            self.current_status = "critical"
            self.logger.error("Status changed to critical")

    def operating(self):

        
        if self.current_status != "operating":
            self.lightthread.color = [50, 50, 50] # white
            self.lightthread.mode = 6 # slow pulse
            self.current_status = "operating"
            self.logger.info("Status changed to operating")

    def success(self):

        
        if self.current_status != "success":
            self.lightthread.mode = 1 # rgb cylce funtime
            self.current_status = "success"
            self.logger.info("Status changed to success")


    def snap(self):

        self.lightthread.notify()

    def initial_engage(self):

        if self.current_status != "initial_engage":

            self.lightthread.mode = 2
            self.lightthread.color = [0,0,100] #blue
            self.current_status = "intial_engage"
            self.logger.info("Status changed to initial_engage")

    def cleanup(self):
        #self.lightthread.join()
        self.lite.cleanup()



class Knob():

    def __init__(   self, 
                    pin=0,
                    adc="",
                    mode=config.ADC_KNOB_SWEEP,
                    selections=0,
                    sweep_range=[0,1],
                    threshold=config.ADC_KNOB_THRESHOLD,
                    knob_hi=config.ADC_KNOB_HI,
                    knob_lo=config.ADC_KNOB_LO,
                    translate_mode="LINEAR"):
        
        self.pin = pin
        self.adc = adc
        self.mode = mode
        self.selections = selections
        self.sweep_range = sweep_range
        self.threshold = threshold
        self.knob_hi = knob_hi
        self.knob_lo = knob_lo
        self.gain = config.ADC_GAIN
        self.translate_mode = translate_mode

        self.rising_time = 0
        self.falling_time = 0

    def get_selection(self):
        
        value = self.adc.read_adc(self.pin, gain=self.gain)

        selection = int(round(helpers.translate(value, self.knob_hi, self.knob_lo, 1, self.selections)))

        return selection


    def get_value(self):

        value = self.adc.read_adc(self.pin, gain=self.gain)

        mapped_value = helpers.translate(value, self.knob_lo, self.knob_hi, self.sweep_range[0],self.sweep_range[1], self.translate_mode)

        return mapped_value

    def cleanup(self):

        return True




class Switch():

    def __init__(   self,
                    pi="",
                    switch_pin=0,
                    callbacks=[],
                    mode="BUTTON",
                    glitch=100):
    
        self.pi = pi
        self.switch_pin = switch_pin
        self.callbacks = callbacks
        self.button_engaged = False
        self.mode = mode
        pi.set_mode(switch_pin, pigpio.INPUT)
        pi.set_glitch_filter(switch_pin, glitch)

        self._start()


    def _start(self):

        if self.mode == "BUTTON":
            cb1 = self.pi.callback(self.switch_pin, pigpio.EITHER_EDGE, self.button_callback)

        elif self.mode == "TOGGLE":
            cb1 = self.pi.callback(self.switch_pin, pigpio.EITHER_EDGE, self.toggle_callback)

    def button_callback(self, GPIO, level, tick):

        index = 1

        if level == 1:
            self.rising_time = tick
            self.button_engaged = True

        elif level == 0:

            self.button_engaged = False
            self.falling_time = tick

            press_time = self.falling_time - self.rising_time
            press_time = float(press_time/1000000.0)

            print press_time

            current_high = -1.0
            chosen_dict = {}

            for func in self.callbacks:


                if func["time"] <= press_time and func["time"] > current_high:

                    current_high = func["time"]
                    chosen_dict = func

            callback_function = chosen_dict["function"]

            try:

                args = chosen_dict["args"]

            except KeyError:

                args = []

            callback_function(*args)

    def toggle(self, GPIO, level, tick):

        if self.pi.read(self.switch_pin):

            callback_function = self.callbacks[1]["function"]

            try:
                
                args = self.callback_function[1]["args"]
            
            except KeyError:

                args = []

            callback_function(*args)

        else:

            callback_function = self.callbacks[0]["function"]

            try:

                args = self.callbacks[0]["args"]

            except KeyError:

                args = []

            callback_function(*args)

    def cleanup(self):

        cb1.cancel()








