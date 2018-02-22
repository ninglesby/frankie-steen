import pigpio
import time

import config


def printerize(GPIO, level, tick):

    print "GPIO=%s   level=%s   tick=%s" % (str(GPIO), str(level), str(tick))

pi  = pigpio.pi()

pi.set_mode(25, pigpio.INPUT)

pi.callback(25, pigpio.EITHER_EDGE, printerize)



time.sleep(60)