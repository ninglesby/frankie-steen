import logging
import threading

import RPi.GPIO as GPIO



def set_gpio_mode():
	# set mode, I don't remember the other mode right now
	if config.GPIO_MODE == "BCM":

		GPIO.setmode(GPIO.BCM)

		return False

	else:

		GPIO.setmode(GPIO.BCM)

		return "Unknown GPIO mode, setting to BCM"

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
		logger.addHandler(self.ch)
		logger.addHandler(self.fh)



# a thread class

# a thread class to allow asynchronous changes to the light
class LightThread(threading.Thread):
	
	def __init__(self, name='LightThread', lite=False):
		""" constructor, setting initial variables """
		#MODE 0: Off
		#MODE 1: Cycle through all the hues at 100% brightness
		#MODE 2: Constant Color
		#MODE 3: Slow Blink
		#MODE 4: Medium Blink
		#MODE 5: Fast Blink
		#MODE 6: Slow Pulse
		#MODE 7: Medium Pulse
		#MODE 8: Fast Pulse
		self._stopevent = threading.Event( )
		self._sleepperiod = 1.0
		self.counter = 0
		self.mode = 0
		self.lite = lite
		self.color = [0,0,0]
		self.break_routine = False
		self.current_mode = 0
		threading.Thread.__init__(self, name=name)

	def run(self):

		on = True

		while not self._stopevent.isSet():

			self.current_mode = self.mode
			
			if not self.mode == 0:
				on = True
				
				# cyle through all the hues
				while self.mode == 1 and not self._stopevent.isSet(): 

					self.current_mode = self.mode

					for x in range(100):
						if self.mode != self.current_mode or self._stopevent.isSet:
							break
						self.lite.hsl(x, 100, 100)
						time.sleep(.01)
				
				# constant on
				while self.mode == 2 and not self._stopevent.isSet():
					self.current_mode = self.mode
					self.lite.rgb(self.color[0], self.color[1], self.color[2])
					time.sleep(.1)
				
				####BLINKS####	
				while self.mode == 3 and not self._stopevent.isSet():
					self.current_mode = self.mode
					self.blink(r=color[0],g=color[1], b=color[2], speed=1)

				while self.mode == 4 and not self._stopevent.isSet():
					self.current_mode = self.mode
					self.blink(r=color[0],g=color[1], b=color[2], speed=.5)

				while self.mode == 5 and not self._stopevent.isSet():
					self.current_mode = self.mode
					self.blink(r=color[0],g=color[1], b=color[2], speed=.25)


				####PULSES####
				while self.mode == 6 and not self._stopevent.isSet():
					self.current_mode = self.mode
					self.pulse(r=color[0],g=color[1], b=color[2], speed=1, step_size=60)

				while self.mode == 7 and not self._stopevent.isSet():
					self.current_mode= self.mode
					self.pulse(r=color[0],g=color[1], b=color[2], speed=.5, step_size=30)

				while self.mode == 8 and not self._stopevent.isSet():
					self.current_mode= self.mode
					self.pulse(r=color[0],g=color[1], b=color[2], speed=.25, step_size=15)


					
			elif on and self.mode == 0:
				self.current_mode = self.mode
				self.lite.hsl(0,0,0)
				on = False
			else:
				time.sleep(.01)
	
	def blink(self, r=100, g=100, b=100, speed=.5):

		r = r/100.0
		g= g/100.0
		b= b/100.0

		self.lite.rgb(r, g, b)
		time.sleep(speed)
		self.lite.rgb(0, 0, 0)
		time.sleep(speed)

	def pulse(self, r=100.0, g=100.0, b=100.0, speed=.5, step_size=50):

		r = r/100.0
		g= g/100.0
		b= b/100.0

		for x in range(step_size):
			if  self.mode != self.current_mode or self._stopevent.isSet:
				return
			else:

				print math.sin((x*(math.pi/step_size)))*100
				self.lite.rgb()
			time.sleep(speed*2/step_size)

	def join(self, timeout=None):
		# Stop the thread and wait for it to end.
		self._stopevent.set( )
		threading.Thread.join(self, timeout)
		
	def rgbSet(self, led_r, led_g, led_b, r, g, b):
		led_r.ChangeDutyCycle(r)
		led_g.ChangeDutyCycle(g)
		led_b.ChangeDutyCycle(b)


# Controls for RGB light on a raspberry pi
class RGBLightController():
	
	def __init__(self, red=27, green=17, blue=26, freq=200):

		GPIO.setup(red, GPIO.OUT)
		GPIO.setup(green, GPIO.OUT)
		GPIO.setup(blue, GPIO.OUT)
		self.pwm_r = GPIO.PWM(red, freq)
		self.pwm_g = GPIO.PWM(green, freq)
		self.pwm_b = GPIO.PWM(blue, freq)
		
		self.pwm_r.start(0)
		self.pwm_g.start(0)
		self.pwm_b.start(0)
		
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
		
		self.pwm_r.ChangeDutyCycle(rgb["r"])
		self.pwm_g.ChangeDutyCycle(rgb["g"])
		self.pwm_b.ChangeDutyCycle(rgb["b"])

	def rgb(self, r, g, b):

		self.pwm_r.ChangeDutyCycle(r)
		self.pwm_g.ChangeDutyCycle(g)
		self.pwm_b.ChangeDutyCycle(b)
		
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


# class to handle status operations
class Status()

	def __init__(self):

		#initialize lights on the Raspberry Pi
		self.lite = RGBLightController(	red=config.GPIO_STATUS_RED,
										green=config.GPIO_STATUS_GREEN,
										blue=config.GPIO_STATUS_BLUE)

		#initalize light thread
		self.lightthread = LightThread(lite=self.lite)


		self.lightthread.start()

		self.current_status = ""

	def nominal(self):

		lightthread.color = [0,100,0] # green
		lightthread.mode = 2 # constant
		self.current_status = "nominal"

	def warning(self):

		lightthread.color = [75, 75, 0] # yellow
		lightthread.mode = 7 # medium pulse
		self.current_status = "warning"

	def critical(self):

		lightthread.color = [100, 0, 0] # red
		lightthread.mode = 4 # medium blink
		self.current_status = "critical"

	def operating(self)

		lightthread.color = [50, 50, 50] # white
		lightthread.mode = 6 # slow pulse
		self.current_status = "operating"

	def success(self)

		lightthread.mode = 1 # rgb cylce funtime
		self.current_status = "success"