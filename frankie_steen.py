import logging

import config
import physical_control
import interface


def manual_adjustment(frankies_log, status):
	return True

def run_scan(frankies_log, status)
	return True

def shutdown(frankies_log, status)
	return False



def main():

	# Create an instance of the logger
	frankies_log = interface.FrankiesLog().logger

	#set gpio mode status, doesn't return anything if it was successful 
	#returns message if there is an error.
	gpio_mode_status = interface.set_gpio_mode():

	if gpio_mode_status:

		frankies_log.warning(gpio_mode_status)

	# Initialize status object
	status = interface.Status(frankies_log)
	frankies_log.info("Initializing status object")
	status.nominal() # set status to nominal

	# Output logger info
	frankies_log.info("Starting up the frankie_steen")	

	# setup knobs for control
	knob_select = interface.knob_select(config.ADC_KNOB_0)
	knob_spring = interface.knob_spring(config.ADC_KNOB_1)

	toggle_run = interface.toggle(config.GPIO_TOGGLE_RUN)

	btn_power = interface.button(config.GPIO_BTN_POWER)

	stepper_sprocket = physical_control.stepper(	dir=config.GPIO_STEPPER_0_DIR,
													on=config.GPIO_STEPPER_0_ON,
													step=config.GPIO_STEPPER_0_STEP,
													mode0=config.GPIO_STEPPER_0_MODE0,
													mode1=config.GPIO_STEPPER_0_MODE1,
													mode2=config.GPIO_STEPPER_0_MODE2 )

	shutdown = False

	#mainloop
	try:

		while not shutdown:

			while knob_select.get_mode() == 0:




			while knob_select.get_mode() == 1:

				rs = run_scan(frankies_log, status)

				if rs:

					shutdown(rs)

	except KeyboardInterrupt:

		frankies_log.info("Keyboard Interrupt, cleaning up threads and GPIO")

		status.cleanup()
		physical_control.cleanup()

