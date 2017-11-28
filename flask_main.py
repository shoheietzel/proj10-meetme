import flask
from flask import render_template
from flask import request
from flask import url_for
import uuid

import json
import logging

import avail_times

# Date handling
import arrow  # Replacement for datetime, based on moment.js
# import datetime # But we still need time
from dateutil import tz  # For interpreting local times


# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2   # used in oauth2 flow

# Google API for services
from apiclient import discovery

###
# Globals
###
import config
if __name__ == "__main__":
  CONFIG = config.configuration()
else:
  CONFIG = config.configuration(proxied=True)

app = flask.Flask(__name__)
app.debug = CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)
app.secret_key = CONFIG.SECRET_KEY

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = CONFIG.GOOGLE_KEY_FILE  # You'll need this
APPLICATION_NAME = 'MeetMe class project'

#############################
#
#  Pages (routed from URLs)
#
#############################


@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Entering index")
  init_session_values()
  return render_template('index.html')


@app.route("/choose")
def choose():
  """
    We'll need authorization to list calendars
    I wanted to put what follows into a function, but had
    to pull it back here because the redirect has to be a
    'return'
  """
  app.logger.debug("Checking credentials for Google calendar access")
  credentials = valid_credentials()
  if not credentials:
    app.logger.debug("Redirecting to authorization")
    return flask.redirect(flask.url_for('oauth2callback'))

  gcal_service = get_gcal_service(credentials)
  app.logger.debug("Returned from get_gcal_service")
  flask.g.calendars = list_calendars(gcal_service)
  app.logger.debug(flask.g.calendars)

  flask.g.all_events = list_events(gcal_service, flask.g.calendars)
  flask.g.daily_availability = list_daily_availability()

  app.logger.debug("flask.g.all_events")
  app.logger.debug(flask.g.all_events)
  app.logger.debug("flask.g.daily_availability")
  app.logger.debug(flask.g.daily_availability)

  flask.g.daily_availability = avail_times.get_free_times(
      flask.g.all_events, flask.g.daily_availability)

  app.logger.debug("flask.g.daily_availability")
  app.logger.debug(flask.g.daily_availability)

  flask.g.all_events_formatted = organize_times(flask.g.all_events, True)
  flask.g.daily_availability_formatted = organize_times(
      flask.g.daily_availability, False)

  return render_template('index.html')


def organize_times(event_list, add_summary):
  """
 sort in order, format for printing
  """
  date_string_list = []
  event_list = sorted(event_list, key=lambda k: k['start'])

  for event in event_list:
    start = arrow.get(event["start"]).format("HH:mm")
    end = arrow.get(event["end"]).format("HH:mm")
    start_date = arrow.get(event["start"]).format("MM/DD/YYYY")
    end_date = arrow.get(event["end"]).format("MM/DD/YYYY")
    if start_date == end_date:
      date_string = start_date + ": " + start + " to " + end
      if add_summary == True:
        date_string_list.append({
          "date_string": date_string,
          "summary": event['summary']
        })
      else:
        date_string_list.append(date_string)
    else:
      date_string = start_date + ": " + start + " to " + end_date + ": " + end
      if add_summary == True:
        date_string_list.append({
          "date_string": date_string,
          "summary": event['summary']
        })
      else:
        date_string_list.append(date_string)
  return date_string_list


def list_calendars(service):
  """
  Given a google 'service' object, return a list of
  calendars.  Each calendar is represented by a dict.
  The returned list is sorted to have
  the primary calendar first, and selected (that is, displayed in
  Google Calendars web app) calendars before unselected calendars.
  """
  app.logger.debug("Entering list_calendars")
  calendar_list = service.calendarList().list().execute()["items"]
  result = []
  for cal in calendar_list:
    kind = cal["kind"]
    id = cal["id"]
    if "description" in cal:
      desc = cal["description"]
    else:
      desc = "(no description)"
    summary = cal["summary"]
    # Optional binary attributes with False as default
    selected = ("selected" in cal) and cal["selected"]
    primary = ("primary" in cal) and cal["primary"]

    if selected == True:
      result.append(
          {"kind": kind,
           "id": id,
           "summary": summary,
           "selected": selected,
           "primary": primary
           })
  return sorted(result, key=cal_sort_key)


def list_events(service, calendars):
  """
  Gets a list of events, add to respective calendar, and format for printing.
  """
  app.logger.debug("Entering list_events")
  all_events_list = []
  for calendar in calendars:
    page_token = None
    while True:
      events = service.events().list(
          calendarId=calendar["id"], singleEvents=True, orderBy='startTime', pageToken=page_token, timeMin=flask.session['begin_date'], timeMax=flask.session['end_date']).execute()
      app.logger.debug(events)
      # iterate through events
      for event in events["items"]:
        add = True
        # don't list transparent events
        if ("transparency" in event and event["transparency"] == "transparent"):
          add = False
        else:
          # check type of event (dict varies based on this)
          # all day events will overlap working hours
          if "date" in event["start"]:
            start = arrow.get(event["start"]["date"]).replace(tzinfo=flask.session["time_zone"])
            end = arrow.get(event["end"]["date"]).replace(tzinfo=flask.session["time_zone"])
          # event with start time/end time
          elif "dateTime" in event["start"]:
            start = arrow.get(event["start"]["dateTime"])
            end = arrow.get(event["end"]["dateTime"])
            # check if event occurs during working hours
            valid = during_workday(start, end)
            if valid == False:
              add = False
          else:
            raise Exception("unrecognized dateTime format")

        if add == True:  # set dict vals and append
          summary = event["summary"]
          all_events_list.append(
              {"start": start,
               "end": end,
               "summary": summary
               })
          # add event info to appropriate key
      page_token = events.get('nextPageToken')
      if not page_token:
        break
  return all_events_list


def during_workday(start, end):
  """
  Check if event busy time overlaps the workday
  Three cases where even doesn't overlap 9 to 5 period:
    start and end both before 9
    start and end both after 5
    start after 5 and end before 5 and date increment only one day
  """
  event_start_time = arrow.get(start).format("HH")
  event_end_time = arrow.get(end).format("HH")
  begin_time = arrow.get(flask.session["begin_time"]).format("HH")
  end_time = arrow.get(flask.session["end_time"]).format("HH")

  event_start_date = arrow.get(start).format("YYYY-MM-DD")
  shifted_start_date = arrow.get(start).shift(days=1).format("YYYY-MM-DD")
  event_end_date = arrow.get(end).format("YYYY-MM-DD")

  # Don't add events that occur outside of working hours
  # case 1: event that occurs before working hours
  # case 2: event that occurs after working hours
  # case 3: overnight event that occurs between working hours of two days

  if (event_start_time < begin_time and event_end_time < begin_time and event_start_date == event_end_date) or (event_start_time > end_time and event_end_time > end_time and event_start_date == event_end_date) or (event_start_time > end_time and event_end_time < begin_time and shifted_start_date == event_end_date):  # don't want these events
    return False
  else:
    return True


def list_daily_availability():
  """
  creates a dict of free times that we can compare our busy times against
  """
  daily_avail_list = []
  date_start = arrow.get(flask.session['begin_date'])
  date_end = arrow.get(flask.session['end_date']).shift(days=-1)
  time_start = arrow.get(flask.session["begin_time"]).format('HH')
  time_end = arrow.get(flask.session["end_time"]).format('HH')
  time_start_min = arrow.get(flask.session["begin_time"]).format('mm')
  time_end_min = arrow.get(flask.session["end_time"]).format('mm')

                                     # 11/12 - 11/26
  while date_start <= date_end:  # 11/12 9am - 11/26 9am
    start = date_start.shift(hours=int(time_start), minutes=int(
        time_start_min)).replace(tzinfo=flask.session["time_zone"])
    end = date_start.shift(hours=int(time_end), minutes=int(
        time_end_min)).replace(tzinfo=flask.session["time_zone"])
    daily_avail_list.append({
        "start": start,
        "end": end
    })
    date_start = arrow.get(next_day(date_start))
  return daily_avail_list

#####


@app.route('/setrange', methods=['POST'])
def setrange():
  """
  User chose a date range with the bootstrap daterange
  widget.
  """
  app.logger.debug("Entering setrange")
  # setting working hours
  start_num = request.form.get('start_num')
  end_num = request.form.get('end_num')
  flask.session["time_zone"] = request.form.get('time_zone')
  flask.session["begin_time"] = interpret_time(start_num)
  flask.session["end_time"] = interpret_time(end_num)
  flask.session["display_begin_time"] = arrow.get(
      flask.session["begin_time"]).format("HH:mm")
  flask.session["display_end_time"] = arrow.get(
      flask.session["end_time"]).format("HH:mm")

  flask.flash("Setrange gave us '{}'".format(
      request.form.get('daterange')))
  daterange = request.form.get('daterange')

  flask.session['daterange'] = daterange
  daterange_parts = daterange.split()
  app.logger.debug(daterange_parts[0])
  app.logger.debug(daterange_parts[1])
  app.logger.debug(daterange_parts[2])
  flask.session['begin_date'] = interpret_date(daterange_parts[0], False)
  flask.session['end_date'] = interpret_date(daterange_parts[2], True)
  app.logger.debug("Setrange parsed {} - {}  dates as {} - {}".format(
      daterange_parts[0], daterange_parts[1],
      flask.session['begin_date'], flask.session['end_date']))

  return flask.redirect(flask.url_for("choose"))

####
#   Initialize session variables
####


def init_session_values():
  """
  Start with some reasonable defaults for date and time ranges.
  Note this must be run in app context ... can't call from main.
  """
  app.logger.debug("entering init_session_values")
  # Default date span = tomorrow to 1 week from now
  now = arrow.now('local')     # We really should be using tz from browser
  tomorrow = now.replace(days=+1)
  nextweek = now.replace(days=+7)

  flask.session["time_zone"] = "US/Pacific"
  app.logger.debug(flask.session["time_zone"])

  flask.session["begin_date"] = tomorrow.floor('day').isoformat()
  flask.session["end_date"] = nextweek.ceil('day').isoformat()
  flask.session["daterange"] = "{} - {}".format(
      tomorrow.format("MM/DD/YYYY"),
      nextweek.format("MM/DD/YYYY"))
  # Default time span each day, 9 to 5
  flask.session["begin_time"] = interpret_time("9am")
  flask.session["end_time"] = interpret_time("5pm")
  # flask session values formatted to display
  flask.session["display_begin_time"] = arrow.get(
      flask.session["begin_time"]).format("HH:mm")
  flask.session["display_end_time"] = arrow.get(
      flask.session["end_time"]).format("HH:mm")
  flask.session["time_zone"] = "US/Pacific"
  app.logger.debug(flask.session["time_zone"])


####
  #
  #  Google calendar authorization:
  #      Returns us to the main /choose screen after inserting
  #      the calendar_service object in the session state.  May
  #      redirect to OAuth server first, and may take multiple
  #      trips through the oauth2 callback function.
  #
  #  Protocol for use ON EACH REQUEST:
  #     First, check for valid credentials
  #         Get credentials (jump to the oauth2 protocol)
  #         (redirects back to /choose, this time with credentials)
  #     If we do have valid credentials
  #         Get the service object
  #
  #  The final result of successful authorization is a 'service'
  #  object.  We use a 'service' object to actually retrieve data
  #  from the Google services. Service objects are NOT serializable ---
  #  we can't stash one in a cookie.  Instead, on each request we
  #  get a fresh serivce object from our credentials, which are
  #  serializable.
  #
  #  Note that after authorization we always redirect to /choose;
  #  If this is unsatisfactory, we'll need a session variable to use
  #  as a 'continuation' or 'return address' to use instead.
  #
  ####

def valid_credentials():
  """
  Returns OAuth2 credentials if we have valid
  credentials in the session.  This is a 'truthy' value.
  Return None if we don't have credentials, or if they
  have expired or are otherwise invalid.  This is a 'falsy' value.
  """
  if 'credentials' not in flask.session:
    return None

  credentials = client.OAuth2Credentials.from_json(
      flask.session['credentials'])

  if (credentials.invalid or
          credentials.access_token_expired):
    return None
  return credentials


def get_gcal_service(credentials):
  """
  We need a Google calendar 'service' object to obtain
  list of calendars, busy times, etc.  This requires
  authorization. If authorization is already in effect,
  we'll just return with the authorization. Otherwise,
  control flow will be interrupted by authorization, and we'll
  end up redirected back to /choose *without a service object*.
  Then the second call will succeed without additional authorization.
  """
  app.logger.debug("Entering get_gcal_service")
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('calendar', 'v3', http=http_auth)
  app.logger.debug("Returning service")
  return service


@app.route('/oauth2callback')
def oauth2callback():
  """
  The 'flow' has this one place to call back to.  We'll enter here
  more than once as steps in the flow are completed, and need to keep
  track of how far we've gotten. The first time we'll do the first
  step, the second time we'll skip the first step and do the second,
  and so on.
  """
  app.logger.debug("Entering oauth2callback")
  flow = client.flow_from_clientsecrets(
      CLIENT_SECRET_FILE,
      scope=SCOPES,
      redirect_uri=flask.url_for('oauth2callback', _external=True))
  # Note we are *not* redirecting above.  We are noting *where*
  # we will redirect to, which is this function.

  # The *second* time we enter here, it's a callback
  # with 'code' set in the URL parameter.  If we don't
  # see that, it must be the first time through, so we
  # need to do step 1.
  app.logger.debug("Got flow")
  if 'code' not in flask.request.args:
    app.logger.debug("Code not in flask.request.args")
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
    # This will redirect back here, but the second time through
    # we'll have the 'code' parameter set
  else:
    # It's the second time through ... we can tell because
    # we got the 'code' argument in the URL.
    app.logger.debug("Code was in flask.request.args")
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    flask.session['credentials'] = credentials.to_json()
    # Now I can build the service and execute the query,
    # but for the moment I'll just log it and go back to
    # the main screen
    app.logger.debug("Got credentials")
    return flask.redirect(flask.url_for('choose'))


def interpret_time(text):
  """
  Read time in a human-compatible format and
  interpret as ISO format with local timezone.
  May throw exception if time can't be interpreted. In that
  case it will also flash a message explaining accepted formats.
  """
  app.logger.debug("Decoding time '{}'".format(text))
  time_formats = ["ha", "h:mma", "h:mm a", "H:mm", "H", "HH", "HH:mm"]
  try:
    as_arrow = arrow.get(text, time_formats).replace(tzinfo=flask.session["time_zone"])
    as_arrow=as_arrow.replace(year=2016)  # HACK see below
    app.logger.debug("Succeeded interpreting time")
  except:
    app.logger.debug("Failed to interpret time")
    flask.flash("Time '{}' didn't match accepted formats 13:30 or 1:30pm"
                .format(text))
    raise
  return as_arrow.isoformat()
  # HACK #Workaround
  # isoformat() on raspberry Pi does not work for some dates
  # far from now.  It will fail with an overflow from time stamp out
  # of range while checking for daylight savings time.  Workaround is
  # to force the date-time combination into the year 2016, which seems to
  # get the timestamp into a reasonable range. This workaround should be
  # removed when Arrow or Dateutil.tz is fixed.
  # FIXME: Remove the workaround when arrow is fixed (but only after testing
  # on raspberry Pi --- failure is likely due to 32-bit integers on that platform)


def interpret_date(text, shift):
  """
  Convert text of date to ISO format used internally,
  with the local time zone.
  Shift takes a boolean. Used to shift the end day so we actually search the proper time range. With the shift, a time range that reads 11/11/17 - 11/11/17 will actually span from 00:00 to 24:00. Original implementation would not span any time, as it was being interpreted as 00:00 to 00:00 on 11/17.
  """
  try:
    as_arrow=arrow.get(text, "MM/DD/YYYY").replace(
        tzinfo=flask.session["time_zone"])
    if shift == True:
      as_arrow=as_arrow.shift(days=1)
  except:
    flask.flash("Date '{}' didn't fit expected format 12/31/2001")
    raise
  return as_arrow.isoformat()


def next_day(isotext):
  """
  ISO date + 1 day (used in query to Google calendar)
  """
  as_arrow=arrow.get(isotext)
  return as_arrow.replace(days=+1).isoformat()

####
#  Functions (NOT pages) that return some information
####


def cal_sort_key(cal):
  """
  Sort key for the list of calendars:  primary calendar first,
  then other selected calendars, then unselected calendars.
  (" " sorts before "X", and tuples are compared piecewise)
  """
  if cal["selected"]:
    selected_key=" "
  else:
    selected_key="X"
  if cal["primary"]:
    primary_key=" "
  else:
    primary_key="X"
  return (primary_key, selected_key, cal["summary"])


#################
#
# Functions used within the templates
#
#################

@app.template_filter('fmtdate')
def format_arrow_date(date):
  try:
    normal=arrow.get(date)
    return normal.format("ddd MM/DD/YYYY")
  except:
    return "(bad date)"


@app.template_filter('fmttime')
def format_arrow_time(time):
  try:
    normal=arrow.get(time)
    return normal.format("HH:mm")
  except:
    return "(bad time)"

#############


if __name__ == "__main__":
  # App is created above so that it will
  # exist whether this is 'main' or not
  # (e.g., if we are running under green unicorn)
  app.run(port=CONFIG.PORT, host="0.0.0.0")
