import os
import json
import pytest
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Add the project root to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from presis.time_tracker import TimeTracker


# Utility function to create test JSON files
def create_test_file(filename, project_name, sessions):
    """Create a test JSON file with the given project name and sessions"""
    os.makedirs(os.path.join(os.path.dirname(__file__), 'assets'), exist_ok=True)
    test_file = os.path.join(os.path.dirname(__file__), 'assets', filename)
    data = {
        "projects": [
            {
                "project_name": project_name,
                "sessions": sessions
            }
        ]
    }
    with open(test_file, 'w') as f:
        json.dump(data, f)
    return test_file

def test_1hour_timesheet_entries():
    # Create a test file with a 1-hour session
    sessions = [
        {
            "start": "01/01/25 - 10:00:00",
            "end": "01/01/25 - 11:00:00",
            "comment": "1 hour test"
        }
    ]
    test_file = create_test_file('test_1_hour.json', "1hour", sessions)
    
    # Initialize TimeTracker with the test file
    tracker = TimeTracker(test_file)
    
    # Test project data
    assert len(tracker.projects) == 1
    assert tracker.projects[0]['project_name'] == "1hour"
    
    # Test total hours calculation
    assert tracker.calculate_total_hours("1hour") == timedelta(seconds=3600)
    assert tracker.calculate_total_hours("1hour").total_seconds() / 3600 == 1

def test_2hour_timesheet_entries():
    # Create a test file with a 2-hour session
    sessions = [
        {
            "start": "01/01/25 - 10:00:00",
            "end": "01/01/25 - 12:00:00",
            "comment": "2 hour test"
        }
    ]
    test_file = create_test_file('test_2_hour.json', "2hour", sessions)
    
    # Initialize TimeTracker with the test file
    tracker = TimeTracker(test_file)
    
    # Test project data
    assert len(tracker.projects) == 1
    assert tracker.projects[0]['project_name'] == "2hour"
    
    # Test total hours calculation
    assert tracker.calculate_total_hours("2hour") == timedelta(seconds=7200)
    assert tracker.calculate_total_hours("2hour").total_seconds() / 3600 == 2

def test_daily_total_timesheet_entries():
    # Create a test file with multiple sessions in a day
    sessions = [
        {
            "start": "01/01/25 - 08:00:00",
            "end": "01/01/25 - 12:00:00",
            "comment": "Morning session"
        },
        {
            "start": "01/01/25 - 13:00:00",
            "end": "01/01/25 - 15:00:00",
            "comment": "Afternoon session 1"
        },
        {
            "start": "01/01/25 - 16:00:00",
            "end": "01/01/25 - 18:00:00",
            "comment": "Afternoon session 2"
        }
    ]
    test_file = create_test_file('test_daily_total.json', "daily_total", sessions)
    
    # Initialize TimeTracker with the test file
    tracker = TimeTracker(test_file)
    
    # Test project data
    assert len(tracker.projects) == 1
    assert tracker.projects[0]['project_name'] == "daily_total"
    
    # Test total hours calculation (should be 8 hours)
    assert tracker.calculate_total_hours("daily_total") == timedelta(seconds=28800)
    assert tracker.calculate_total_hours("daily_total").total_seconds() / 3600 == pytest.approx(8, abs=0.01)
    
    # Test daily hours breakdown
    daily = tracker.assemble_total_hours_per_day("daily_total")
    assert len(daily) == 1  # 1 day
    assert daily[0][1].total_seconds() / 3600 == pytest.approx(8, abs=0.01)  # 8 hours

def test_late_night_timesheet_entries():
    # Create a test file with a session that spans midnight
    sessions = [
        {
            "start": "01/01/25 - 22:00:00",
            "end": "02/01/25 - 02:00:00",
            "comment": "Late night session"
        }
    ]
    test_file = create_test_file('test_late_night.json', "late_night", sessions)
    
    # Initialize TimeTracker with the test file
    tracker = TimeTracker(test_file)
    
    # Test project data
    assert len(tracker.projects) == 1
    assert tracker.projects[0]['project_name'] == "late_night"
    
    # Test total hours calculation (should be 4 hours)
    assert tracker.calculate_total_hours("late_night") == timedelta(seconds=14400)
    assert tracker.calculate_total_hours("late_night").total_seconds() / 3600 == 4
    
    # Test daily hours breakdown
    daily = tracker.assemble_total_hours_per_day("late_night")
    assert len(daily) == 2  # Spans 2 days
    
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
