import logging

import config
import motor_control
import interface

def main():

	# Create an instance of the logger
	frankies_log = interface.FrankiesLog().logger

	# Initialize status object
	status = interface.Status()
	frankies_log.info("Initializing status object")
	status.nominal() # set status to nominal

	# Output logger info
	frankies_log.info("Starting up the frankie_steen")

