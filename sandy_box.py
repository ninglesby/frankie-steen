import math

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


print translate(5, 0, 10, 0, 2, mode="EXP")