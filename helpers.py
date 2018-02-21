import math
import os


import config

class Cleanup():

    def __init__(self, logger):

        self.cleanup_list = []
        self.logger = logger

    def clean_all(self):

        for item in self.cleanup_list:

            self.logger.info("Cleaning up %s" % item.__class__.__name__)

            item.cleanup()

        self.logger.info("Cleanup Complete")

        return


def translate(value, map_from_min, map_from_max, map_to_min, map_to_max, mode="LINEAR"):
    

    # Figure out how 'wide' each range is
    from_span = map_from_max - map_from_min
    to_span = map_to_max - map_to_min

    # Convert the left range into a 0-1 range (float)
    value_scaled = float(value - map_from_min) / float(from_span)
    

    if mode == "LINEAR":

        # Convert the 0-1 range into a value in the right range.
        return map_to_min + (value_scaled * to_span)

    elif mode == "LOG":

        if value_scaled < .01:
            
            return 0

        log = ((math.log(value_scaled, 10))+2)/2

        return map_to_min + (log * to_span)

    elif mode == "EXP":

        exp = math.pow(value_scaled, 2)

        return map_to_min + (exp * to_span)


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