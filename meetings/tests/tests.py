"""
Nose tests for avail_times.py
"""
import flask_main
import avail_times
import arrow

import nose    # Testing framework
import logging
logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.WARNING)
log = logging.getLogger(__name__)


def test_1():
    """
    trivial cases: return daily_avail if no events

    """
    events = []
    daily_avail = [{'start': "2017-11-01T09:00:00-07:00",
                    'end': "2017-11-01T12:00:00-07:00"}]

    assert avail_times.get_free_times(events, daily_avail) == [
        {'start': "2017-11-01T09:00:00-07:00", 'end': "2017-11-01T12:00:00-07:00"}]


def test_2():
    """
    Tests for all-day event, should be no available times
    """
    events = [{'start': "2017-11-13T00:00:00-08:00",
               'end': "2017-11-14T00:00:00-08:00", 'summary': 'An all day event'}]
    daily_avail = [{'start': "2017-11-13T09:00:00-08:00",
                    'end': "2017-11-13T12:00:00-08:00"}]
    assert avail_times.get_free_times(events, daily_avail) == []


def test_3():
    """
    Tests for multi-day event, from 00 on 11/13 to 10 on 11/15
    Assuming working hours of 9-17, should return avail of 10 to 17 on 11/15
    """
    events = [{'start': "2017-11-13T00:00:00-08:00",
               'end': "2017-11-15T10:00:00-08:00", 'summary': 'multi-day event'}]
    daily_avail = [{'start': "2017-11-13T09:00:00-08:00",
                    'end': "2017-11-13T17:00:00-08:00"},
                   {'start': "2017-11-14T09:00:00-08:00",
                    'end': "2017-11-14T17:00:00-08:00"},
                   {'start': "2017-11-15T09:00:00-08:00",
                    'end': "2017-11-15T17:00:00-08:00"}, ]
    assert avail_times.get_free_times(events, daily_avail) == [
        {'start': "2017-11-15T10:00:00-08:00", 'end': "2017-11-15T17:00:00-08:00"}]


def test_4():
    """
    tests for cases A-E in get_free_times logic
    Busy times: 4-6, 8-10, 12-14, 16-18, 20-22
    if working times are 9 to 17, resulting free times should be 10-12 and 14-16
    """
    events = [{'start': "2017-11-13T04:00:00-08:00",
               'end': "2017-11-13T06:00:00-08:00", 'summary': 'CASE A'},
              {'start': "2017-11-13T08:00:00-08:00",
               'end': "2017-11-13T10:00:00-08:00", 'summary': 'CASE B'},
              {'start': "2017-11-13T12:00:00-08:00",
               'end': "2017-11-13T14:00:00-08:00", 'summary': 'CASE C'},
              {'start': "2017-11-13T16:00:00-08:00",
               'end': "2017-11-13T18:00:00-08:00", 'summary': 'CASE D'},
              {'start': "2017-11-13T20:00:00-08:00",
               'end': "2017-11-13T22:00:00-08:00", 'summary': 'CASE E'}]
    daily_avail = [{'start': "2017-11-13T09:00:00-08:00",
                    'end': "2017-11-13T17:00:00-08:00"}]
    assert avail_times.get_free_times(events, daily_avail) == [{'start': '2017-11-13T10:00:00-08:00', 'end': '2017-11-13T12:00:00-08:00'}, {
        'start': '2017-11-13T14:00:00-08:00', 'end': '2017-11-13T16:00:00-08:00'}]


def test_5():
    """
    same test as 4 but with different working hours
    tests for cases A-E in get_free_times logic
    Busy times: 4-6, 8-10, 12-14, 16-18, 20-22
    if working times are 00:00 to 23:59, resulting free times should be 0-4, 6-8, 10-12, 14-16, 18-20, 22-23:59
    """
    events = [{'start': "2017-11-13T04:00:00-08:00",
               'end': "2017-11-13T06:00:00-08:00", 'summary': 'CASE A'},
              {'start': "2017-11-13T08:00:00-08:00",
               'end': "2017-11-13T10:00:00-08:00", 'summary': 'CASE B'},
              {'start': "2017-11-13T12:00:00-08:00",
               'end': "2017-11-13T14:00:00-08:00", 'summary': 'CASE C'},
              {'start': "2017-11-13T16:00:00-08:00",
               'end': "2017-11-13T18:00:00-08:00", 'summary': 'CASE D'},
              {'start': "2017-11-13T20:00:00-08:00",
               'end': "2017-11-13T22:00:00-08:00", 'summary': 'CASE E'}]
    daily_avail = [{'start': "2017-11-13T00:00:00-08:00",
                    'end': "2017-11-13T23:59:00-08:00"}]
    assert avail_times.get_free_times(events, daily_avail) == [{'start': '2017-11-13T00:00:00-08:00', 'end': '2017-11-13T04:00:00-08:00'}, {'start': '2017-11-13T06:00:00-08:00', 'end': '2017-11-13T08:00:00-08:00'}, {'start': '2017-11-13T10:00:00-08:00', 'end': '2017-11-13T12:00:00-08:00'},
                                                               {'start': '2017-11-13T14:00:00-08:00', 'end': '2017-11-13T16:00:00-08:00'}, {'start': '2017-11-13T18:00:00-08:00', 'end': '2017-11-13T20:00:00-08:00'}, {'start': '2017-11-13T22:00:00-08:00', 'end': '2017-11-13T23:59:00-08:00'}, ]
