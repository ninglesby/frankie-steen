######LOGGING SETTINGS##########

LOG_LOCATION = "/var/logs/frankie-steen.log"
LOG_VERBOSITY = 10 #DEBUG 10, INFO 20, WARNING 30, ERROR 40, CRITICAL 50 -OUTPUT to file
LOG_SHELL_VERBOSITY = 20 #Level of verbosity for what shows up in the shell
LOG_NAME = "frankie-steen"

#####STEPPER SETTTINGS#######

STEPPER_RES = "1" #The resolution of the stepper motor could be 1, 1/2, 1/4. 1/8. 1/16. 1/32
STEPPER_MAX = 0.004 #The fastest speed the stepper motor can go before chopping
STEPPER_MIN = 1 #The lowest reasonable speed for the stepper
STEPPER_DEFAULT = .01 #Speed for default operations


#####GPIO PINOUT######

GPIO_MODE = "BCM"

GPIO_STEPPER_0_DIR = 1
GPIO_STEPPER_0_ON =  2
GPIO_STEPPER_0_STEP = 6
GPIO_STEPPER_0_MODE0 = 3
GPIO_STEPPER_0_MODE1 = 4
GPIO_STEPPER_0_MODE2 = 5

GPIO_STATUS_RED = 7
GPIO_STATUS_GREEN = 8
GPIO_STAUS_BLUE = 9

GPIO_TOGGLE_RUN = 10
GPIO_BTN_POWER = 11
GPIO_BTN_CALIBRATE = 12

#####ADC CHANNEL####

ADC_KNOB_0 = 0
ADC_KNOB_1 = 1
ADC_PHOTOSENSOR_0 = 2
ADC_PHOTOSENSOR_1 = 4

ADC_KNOB_THRESHOLD = 80