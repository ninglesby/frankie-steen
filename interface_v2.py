import logging
import threading
import time
import subprocess
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import RPi.GPIO as GPIO
import pigpio
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

import config
import helpers
import interface_v2 as interface


class Display():
    def __init__(self):
        """ constructor, setting initial variables """
        self._sleepperiod = 1.0
        self.counter = 0
        self.mode = 0
        self.text = []
        self.text_str = ""
        self.title = ""
        self.endloop = False
        # Raspberry Pi pin configuration:
        RST = None     # on the PiOLED this pin isnt used
        # Note the following are only used with SPI:
        DC = 23
        SPI_PORT = 0
        SPI_DEVICE = 0

        # Beaglebone Black pin configuration:
        # RST = 'P9_12'
        # Note the following are only used with SPI:
        # DC = 'P9_15'
        # SPI_PORT = 1
        # SPI_DEVICE = 0

        # 128x32 display with hardware I2C:
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

        # 128x64 display with hardware I2C:
        # disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

        # Note you can change the I2C address by passing an i2c_address parameter like:
        # disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)

        # Alternatively you can specify an explicit I2C bus number, for example
        # with the 128x32 display you would use:
        # disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, i2c_bus=2)

        # 128x32 display with hardware SPI:
        # disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

        # 128x64 display with hardware SPI:
        # disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

        # Alternatively you can specify a software SPI implementation by providing
        # digital GPIO pin numbers for all the required display pins.  For example
        # on a Raspberry Pi with the 128x32 display you might use:
        # disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, sclk=18, din=25, cs=22)

        # Initialize library.
        self.disp.begin()

        # Clear display.
        self.disp.clear()
        self.disp.display()

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new('1', (self.width, self.height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # Draw a black filled box to clear the image.
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)

        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        self.padding = -2
        self.top = self.padding
        self.bottom = self.height-self.padding
        # Move left to right keeping track of the current x position for drawing shapes.
        self.x = 0
        self.y=0

        # Load default font.
        self.font = ImageFont.load_default()
        self.alt_font = ImageFont.truetype(font="/home/pi/workspace/frankie-steen/monofonto.ttf", size=10, index=0)

    def stats(self):

        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)

        # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
        cmd = "hostname -I | cut -d\' \' -f1"
        IP = subprocess.check_output(cmd, shell = True )
        cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
        CPU = subprocess.check_output(cmd, shell = True )
        cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
        MemUsage = subprocess.check_output(cmd, shell = True )
        cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
        Disk = subprocess.check_output(cmd, shell = True )

        # Write two lines of text.

        #self.draw.text((self.x, self.top),       "IP: " + str(IP),  font=self.alt_font, fill=255)
        self.draw.text((self.x, self.top),     str(CPU), font=self.font, fill=255)
        self.draw.text((self.x, self.top+8),    str(MemUsage),  font=self.font, fill=255)
        #self.draw.text((self.x, self.top+25),    str(Disk),  font=self.alt_font, fill=255)

        # Display image.
        self.disp.image(self.image)
        self.disp.display()

    def scroll(self, text):

        if text:
            for line in self.line_split(text):
                self.text.append(line)

            self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
            
            try:
                self.draw.text((0, 0), self.title, font=self.font, fill=255)
                for n in range(6):
                    
                    self.draw.text((0, ((n)*8)+14),       self.text[0-(n+1)],  font=self.font, fill=255)

            except IndexError:

                pass

            if not self.endloop:
                self.disp.image(self.image)
                self.disp.display()

    def message(self, text=[], title=""):

        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
        if title:
            self.title = title    
        
        self.draw.text((0, 0), self.title, font=self.font, fill=255)
        if text:
            self.text = text

        else:

            n = 0
            for line in self.text:
                self.draw.text((0, ((n)*8)+14),       self.text[0-(n+1)],  font=self.font, fill=255)
                n += 1    

        if not self.endloop:
            self.disp.image(self.image)
            self.disp.display()           


    def line_split(self, text, line_length=19, reverse=True):

        line_list = []

        if len(text) > line_length:

            lines = float(len(text))/float(line_length)

            if float(lines) > float(int(lines)):

                lines = int(lines) + 1

            else:
            
                lines = int(lines)       

            for line in range(lines):

                if line != lines-1:

                    line_list.append((text[line_length*line:line_length*(line+1)])+"-")

                else:

                    line_list.append(text[line_length*line:])
        else:
            line_list.append(text)

        if reverse:
            temp_list = []
            for line in range(len(line_list)):
                temp_list.append(line_list[(line+1)*-1])
            line_list = temp_list
        
        return line_list


    def cleanup(self):
            print "cleaning up"
            self.endloop = True
            self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
            self.disp.image(self.image)
            self.disp.display()
            time.sleep(.1)

#A logging class for better debugging over just printing to the console
class ScreenHandler(logging.Handler):

    def emit(self, record):
        msg = self.format(record)
        #display = interface.Display()
        self.display.scroll(msg)

    def set_display(self, display):
        self.display = display




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

    def __init__(self, logger="", display=""):

        #initialize lights on the Raspberry Pi
        #self.lite = RGBLightController( logger=logger,
         #                               red=config.GPIO_STATUS_RED,
          #                              green=config.GPIO_STATUS_GREEN,
           #                             blue=config.GPIO_STATUS_BLUE)

        #initalize light thread
        #self.lightthread = LightThread( logger=logger, lite=self.lite)
        #self.lightthread.start()

        self.logger = logger
        self.display = display
        self.display_mode = "SCROLL"
        self.current_status = ""

    def update_display(self, mode=None, title="", text=""):

        if not mode:
            mode = self.display_mode


        if mode == "SCROLL":
            self.display_mode = "SCROLL"
            if title:
                self.display.title = title
            self.display.scroll(text)

        elif mode == "STATS":
            self.display_mode = "STATS"
            self.display.stats()

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
                    name = "Knob",
                    pin=0,
                    adc="",
                    mode=config.ADC_KNOB_SWEEP,
                    selections=0,
                    sweep_range=[0,1],
                    threshold=config.ADC_KNOB_THRESHOLD,
                    knob_hi=config.ADC_KNOB_HI,
                    knob_lo=config.ADC_KNOB_LO,
                    translate_mode="LINEAR"):
        
        self.name = name
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
                    logger="",
                    name="Switch",
                    pi="",
                    switch_pin=0,
                    callbacks=[],
                    mode="BUTTON",
                    glitch=500,
                    PULL_UP_DOWN="DOWN"):
    
        self.logger = logger
        self.name = name
        self.pi = pi
        self.switch_pin = switch_pin
        self.callbacks = callbacks
        self.button_engaged = False
        self.mode = mode
        self.current_chosen_dict = ""
        pi.set_mode(switch_pin, pigpio.INPUT)
        pi.set_glitch_filter(switch_pin, glitch)

        if PULL_UP_DOWN == "DOWN":

            self.ACTIVE = 0
            self.NORMAL = 1

        else:

            self.ACTIVE = 1
            self.NORMAL = 0

        self._start()


    def _start(self):

        if self.mode == "BUTTON":
            self.cb1 = self.pi.callback(self.switch_pin, pigpio.EITHER_EDGE, self.button_callback)

        elif self.mode == "TOGGLE":
            self.cb1 = self.pi.callback(self.switch_pin, pigpio.EITHER_EDGE, self.toggle_callback)

    def button_callback(self, GPIO, level, tick):

        index = 1

        if level == self.ACTIVE:

            self.rising_time = tick
            self.button_engaged = True

        elif level == self.NORMAL:
            self.chosen_dict = ""
            self.button_engaged = False
            self.falling_time = tick

            press_time = self.pi.get_current_tick() - self.rising_time 
            press_time = float(press_time/1000000.0)

            chosen_dict = self.get_function(press_time)

            try:

                callback_function = chosen_dict["function"]

            except KeyError:

                self.logger.warning("No callback for %s" % self.name)

                return
            try:

                args = chosen_dict["args"]

            except KeyError:

                args = []

            callback_function(*args)

    def get_function(self, press_time):

            current_high = -1.0
            chosen_dict = {}

            for func in self.callbacks:


                if func["time"] <= press_time and func["time"] > current_high:

                    current_high = func["time"]
                    chosen_dict = func

            return chosen_dict

    def check_button(self):

        if self.button_engaged:

            press_time = self.pi.get_current_tick() - self.rising_time
            press_time = float(press_time/1000000.0)

            chosen_dict = self.get_function(press_time)

            if chosen_dict != self.current_chosen_dict:

                self.current_chosen_dict = chosen_dict

                try:
                    notify_function = chosen_dict["notify_function"]
                    notify_args = chosen_dict["notify_args"]
                    notify_function(*notify_args)

                except KeyError:

                    pass




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

        self.cb1.cancel()








