######LOGGING SETTINGS##########

LOG_LOCATION = "/var/logs/frankie-steen.log"
LOG_VERBOSITY = 10 #DEBUG 10, INFO 20, WARNING 30, ERROR 40, CRITICAL 50 -OUTPUT to file
LOG_SHELL_VERBOSITY = 20 #Level of verbosity for what shows up in the shell
LOG_NAME = "frankie-steen"
FRAME_COUNT = 0
ROTATION = 0

#####STEPPER SETTTINGS#######

STEPPER_RES = "1" #The resolution of the stepper motor could be 1, 1/2, 1/4. 1/8. 1/16. 1/32
STEPPER_MAX = 0.004 #The fastest speed the stepper motor can go before chopping
STEPPER_MIN = 1 #The lowest reasonable speed for the stepper
STEPPER_DEFAULT = .01 #Speed for default operations
STEPPER_FRAME_DEGREE = 22.5
STEPPER_TOTAL_STEPS = 200



#####GPIO PINOUT######

GPIO_MODE = "BCM"

GPIO_STEPPER_0_DIR = 27
GPIO_STEPPER_0_ON =  17
GPIO_STEPPER_0_STEP = 22
GPIO_STEPPER_0_MODE0 = 10
GPIO_STEPPER_0_MODE1 = 9
GPIO_STEPPER_0_MODE2 = 11

GPIO_STEPPER_1_DIR = 5
GPIO_STEPPER_1_ON =  6
GPIO_STEPPER_1_STEP = 13

GPIO_STATUS_RED = 16
GPIO_STATUS_GREEN = 20
GPIO_STAUS_BLUE = 21

GPIO_TOGGLE_RUN = 12
GPIO_TOGGLE_UPTAKE = 7
GPIO_BTN_POWER = 8
GPIO_BTN_CALIBRATE = 25

GPIO_CAMERA_SHUTTER - 24	

#####ADC CHANNEL####

ADC_KNOB_0 = 0
ADC_KNOB_1 = 1
ADC_PHOTOSENSOR_0 = 2
ADC_PHOTOSENSOR_1 = 4
ADC_GAIN = 1
ADC_KNOB_SELECT = 0
ADC_KNOB_SWEEP = 1

ADC_KNOB_THRESHOLD = .05

SELECT_MANUAL_ADJUST = 0
SELECT_RUN = 1