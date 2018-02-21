import pigpio
import config


pi = pigpio.pi()

blue = config.GPIO_STATUS_BLUE

pi.write(blue, 1)

pi.stop()