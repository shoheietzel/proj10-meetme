# Project 10: MeetMe #
### Author: Shohei Etzel, sse@uoregon.edu ###
### https://mighty-scrubland-35462.herokuapp.com/ ###

# Summary
A meeting organizer program that polls for user free times so that a meeting admin can make an informed decision on when to make a meeting.

# Ideology
My goal was to make a minimal working version of the meetme program that could be used as a legitimate meeting organizer from start to finish. In order to create this, the program does assume that users will act as expected. I am sure that some fringe cases/unexpected behaviors are not handled. This program also forces to user to manually perform some of the process, such as e-mailing the links and choosing which freetimes work for them. I actually prefer to have the users maually enter which time slots work for them; they may have a preferance of which free time they actually are willing to commit to a meeting.

If I were to continue on this, I would allow an admin to determine a meeting duration. As of now, if a free time slot was 4 hours, the meeting time would either be that whole 4 hours, or none of it. I would also like to add some graphical interface to the existing one, so free times can be better visualized. One last thing I would add is support for all timezones. I was forced to make an extra slot to specify a timezone because of Heroku deployment, and I could not get support for multiple timezones working in time.

# Deployment (locally/Heroku)
This program can be run locally like our other projects with the addition of a google client key, mLab key, and credentials file (just like previous projects).
It is also running on Heroku at: https://mighty-scrubland-35462.herokuapp.com/

# Functionality/Features 
### Creating a meeting ###
    - Select daily start time/end time/time zone/date range 
        *(currently only US/Pacific tz support)
    - Select which calendar events to display
    - Select meeting time from free time slots (Busy time list from GCal below)
        *(no support yet for meeting duration within each slot)
    - Init meeting sends user to meeting confirmation page, w/user and admin links
        (Local server links are meant just for testing, the program is also up and running on heroku)
        (Links are meant to be copied and e-mailed)
### Viewing a meeting (user) ###
    - Users can view their own openings from selected calendars, daterange, tz, etc.
    - After comparing open times and meeting times side-by-side, users can select which slots they are willing to meet up for
    - Users will also sign their name so the admin can view who has responded and when they can meet up
    - An "update successful" page will notify the user once their form is submitted
    - A user can check up on meeting status anytime; a finalized meeting will show the meeting status and the determined time (or the cancellation)
### Viewing a meeting (admin) ###
    - An admin's meeting page shows much more information
    - Each time slot is listed in a drop down menu, with any responses from co-workers
    - The admin can then select a slot to finalize the meeting (or cancel it)
    - Upon finalization, the page redirects to the same already_finalized page that the users will now see

# Versions 
### Version 1.1 ###
Added meeting finalization and cancellation

### Version 1.0 ###
Basic working functionality

# Running
Go to folder you want to download on the command line.

Type 'git clone https://github.com/shoheietzel/proj10-meetme' to download

To start the server, go to the main repository and type commands 'make install' (for first time users) and then 'make run' into the terminal. To stop the server, type Ctrl + c.

