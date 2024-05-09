import os
import json
import pytest
from ..cinner import Cinner
from datetime import datetime, timedelta
from collections import defaultdict


def test_1hour_timesheet_entries():
    test_file = os.path.join(os.path.dirname(__file__), 'assets', 'test_1_hour.json')
    cinner = Cinner(test_file)
    entries = cinner.load_data(test_file)
    # print(entries)
    assert len(entries) == 1
    assert entries['projects'][0]['project_name'] == "1hour"
    # assert cinner.has_ongoing_sessions("1hour") == False
    # assert cinner.get_total_timedelta("1hour") == timedelta(seconds=3600)
    assert cinner.calculate_total_hours("1hour") == timedelta(seconds=3600)
    assert cinner.calculate_total_hours("1hour").total_seconds() / 3600 == 1

def test_2hour_timesheet_entries():
    test_file = os.path.join(os.path.dirname(__file__), 'assets', 'test_2_hour.json')
    cinner = Cinner(test_file)
    entries = cinner.load_data(test_file)
    # print(entries)
    assert len(entries) == 1
    assert entries['projects'][0]['project_name'] == "2hour"
    # assert cinner.has_ongoing_sessions("2hour") == False
    # assert cinner.get_total_timedelta("2hour") == timedelta(seconds=7200)
    assert cinner.calculate_total_hours("2hour") == timedelta(seconds=7200)
    assert cinner.calculate_total_hours("2hour").total_seconds() / 3600 == 2

def test_daily_total_timesheet_entries():
    test_file = os.path.join(os.path.dirname(__file__), 'assets', 'test_daily_total.json')
    cinner = Cinner(test_file)
    entries = cinner.load_data(test_file)
    # print(entries)
    assert len(entries) == 1
    assert entries['projects'][0]['project_name'] == "daily_total"
    # assert cinner.has_ongoing_sessions("daily_total") == False
    # assert cinner.get_total_timedelta("daily_total") == timedelta(seconds=21599, microseconds=999997)
    assert cinner.calculate_total_hours("daily_total") == timedelta(seconds=21600)
    assert cinner.calculate_total_hours("daily_total").total_seconds() / 3600 == pytest.approx(6, abs=0.01)
    daily = cinner.assemble_total_hours_per_day("daily_total")
    # print(daily)
    assert daily

def test_late_night_timesheet_entries():
    test_file = os.path.join(os.path.dirname(__file__), 'assets', 'test_late_night.json')
    print(f'starting test with file: {test_file}')
    cinner = Cinner(test_file)
    entries = cinner.load_data(test_file)
    print(entries)
    assert len(entries) == 1
    assert entries['projects'][0]['project_name'] == "late_night"
    # assert cinner.has_ongoing_sessions("late_night") == False
    # assert cinner.get_total_timedelta("late_night") == timedelta(seconds=21599)
    # assert cinner.calculate_total("late_night") == timedelta(seconds=21599)
    # assert cinner.calculate_total("late_night").total_seconds() / 3600 == 6
    daily = cinner.assemble_total_hours_per_day("late_night")
    print(daily)
    assert daily
    
# def test_split_hours_per_day(plotter):
#     start = "01/04/24 - 22:06:01"
#     end = "02/04/24 - 00:51:08"
#     result = plotter.split_hours_per_day(start, end)
#     expected = defaultdict(float, {1: 1.9, 2: 2.8})
#     assert result == expected

# def test_get_total_hours_per_day(plotter):
#     daily_hours = plotter.get_total_hours_per_day()
#     expected = defaultdict(float, {1: 1.9, 2: 8.5})
#     assert daily_hours == expected
