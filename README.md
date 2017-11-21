# Project 8: Google Calendar Free Times #
### Author: Shohei Etzel, sse@uoregon.edu ###

### Summary ###
Takes a user's Google Calendars and lists all the free times, derived from selected calendar's events*.

*calendar selection functionality currently not included

### Features ###
Type in your preferred date range and starting and end times for each day (i.e. working hours). All corresponding events during that range will occur, giving you all the times you are busy between your selected "working hours". It then looks at all of those events and also returns free times.

### Running ###
Go to folder you want to download on the command line.

Type 'git clone https://github.com/shoheietzel/proj8-Freetimes' to download

To start the server, go to the main repository and type commands 'make install' (for first time users) and then 'make run' into the terminal. To stop the server, type Ctrl + c.

### Testing ###
Type 'make test' to run the nose tests (tests.py) in the tests folder.
