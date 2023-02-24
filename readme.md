# QuizBox 0.5

## Current Status:
- Workingish. Seats/switches/display are working, reset is not, buzzer has not been tested, and box-to-box hasn't been developed.



## Parts
- Seatpad (x5)
- Disable Switch (x5)
- 12 LEDs
	- 5 pairs for quizzer seat lights
	- Quizzer boxState light
	- Quizmaster boxState light
- RESET switch
- 2004 LCD Character display
- Pizo buzzer
- internal
	- RPi Pico W
	- TLC5947
	- USB-C box-to-box connector

## Features (*italicized* arn't done yet)
- Hardware is configured
	- Seats/Switches/Reset
	- Display
	- TLC5947
	- *Box-to-Box*
- Quizzer leds are toggled based on disable switches and seatpads
- QuizBox can be armed so that when a quizzer jumps, it beeps and a timer is started
- *Online Features*
	- Current state is reported to the cloud (quizbox.app on DigitalOcean)
	- QuizBox can be controlled remotely
