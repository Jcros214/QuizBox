# QuizBox 0.5

## Current Status:
- Workingish. Seats/switches/display/reset/buzzer are working,  is not, buzzer has not been tested, and box-to-box hasn't been developed.

## Ideas
- Serial communication between boxes?
	- All that's needes is shared ground and Tx/Rx
- Just use the micro usb port on the front for data output
	- Can be made to work with a computer/phone
	- Input...
		- Test pins?

## Features (*italicized* arn't done yet)
- Hardware
	- Seats/Switches/Reset
	- Display
	- TLC5947
	- *Box-to-Box*
- Quizzer leds are toggled based on disable switches and seatpads
- QuizBox can be armed so that when a quizzer jumps, it beeps and a timer is started
- *Online Features*
	- Current state is reported to the cloud (quizbox.app on DigitalOcean)
	- QuizBox can be controlled remotely
