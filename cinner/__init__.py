#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import argparse
from datetime import datetime, timedelta
from functools import reduce
from collections import defaultdict


class Cinner:
    def __init__(self, json_file):
        self.json_file = json_file
        self.projects = self.load_data(json_file).get("projects", [])

    def load_data(self, path):
        """Reads the data from a JSON file."""
        if not path or not os.path.exists(path):
            return {"projects": []}
        with open(path, "r") as f:
            return json.load(f)

    def save_data(self):
        """Writes the data to a JSON file."""
        with open(self.json_file, "w+") as f:
            json.dump({"projects": self.projects}, f, indent=2)

    def new_session(self):
        """Creates a new working session dictionary."""
        return {"start": self.current_timestamp(), "end": None}

    def current_timestamp(self):
        """Returns the current timestamp with a specific format."""
        return datetime.now().strftime("%d/%m/%y - %H:%M:%S")

    def get_project(self, project_name):
        """Finds a specific project in the projects list."""
        return next((p for p in self.projects if p["project_name"] == project_name), None)

    def add_or_update_project(self, project_name):
        """Creates a new project or adds a timestamp to an existing one."""
        project = self.get_project(project_name)
        if not project:
            project = {"project_name": project_name, "sessions": [self.new_session()]}
            self.projects.append(project)
        else:
            last_session = project["sessions"][-1]
            if last_session["end"] is None:
                last_session["end"] = self.current_timestamp()
            else:
                project["sessions"].append(self.new_session())
        self.save_data()

    def calculate_daily_hours(self, sessions, target_date):
        """Calculate the total number of hours worked on a given day, considering overlaps."""
        fmt = "%d/%m/%y - %H:%M:%S"
        target_day = datetime.strptime(target_date, "%d/%m/%y").date()
        intervals = []

        for session in sessions:
            start_time = datetime.strptime(session["start"], fmt)
            end_time = datetime.strptime(session["end"], fmt) if session["end"] else datetime.now()

            if start_time.date() <= target_day and end_time.date() >= target_day:
                start_of_day = datetime.combine(target_day, datetime.min.time())
                end_of_day = datetime.combine(target_day, datetime.max.time())

                start_interval = max(start_time, start_of_day)
                end_interval = min(end_time, end_of_day)

                intervals.append((start_interval, end_interval))

        intervals.sort()
        merged_intervals = []
        if intervals:
            current_start, current_end = intervals[0]

            for start, end in intervals[1:]:
                if start <= current_end:
                    current_end = max(current_end, end)
                else:
                    merged_intervals.append((current_start, current_end))
                    current_start, current_end = start, end
            merged_intervals.append((current_start, current_end))

        total_time = timedelta()
        for start, end in merged_intervals:
            total_time += end - start

        return timedelta(seconds=round(total_time.total_seconds()))

    def assemble_total_hours_per_day(self, project_name):
        """Assemble a list of total hours worked in each day."""
        project = self.get_project(project_name)
        if not project:
            return []

        fmt = "%d/%m/%y - %H:%M:%S"
        all_dates = set()

        for session in project["sessions"]:
            start_time = datetime.strptime(session["start"], fmt)
            end_time = datetime.strptime(session["end"], fmt) if session["end"] else datetime.now()

            current_date = start_time.date()
            while current_date <= end_time.date():
                all_dates.add(current_date)
                current_date += timedelta(days=1)

        daily_hours = defaultdict(timedelta)
        for date in sorted(all_dates):
            total_time = self.calculate_daily_hours(project["sessions"], date.strftime("%d/%m/%y"))
            daily_hours[date] = total_time

        return [(date, daily_hours[date]) for date in sorted(daily_hours)]

    def calculate_total_hours(self, project_name):
        """Calculate the total hours worked for a project."""
        daily_totals = self.assemble_total_hours_per_day(project_name)
        total_time = sum((hours for _, hours in daily_totals), timedelta())
        return timedelta(seconds=round(total_time.total_seconds()))

    def print_daily_report(self, project_name):
        """Generate and print a daily report of hours worked per day."""
        daily_totals = self.assemble_total_hours_per_day(project_name)
        print("\n=== Daily Hours Report ===")
        for date, total_time in daily_totals:
            total_hours = total_time.total_seconds() / 3600
            print(f"Total hours worked on {date}: {total_hours:.2f} hours")
        print("==========================")

    def print_total_report(self, project_name):
        """Print a report with the total hours worked for a project."""
        total_hours = self.calculate_total_hours(project_name).total_seconds() / 3600
        print(f"\nTotal hours worked on '{project_name}': {total_hours:.2f} hours for ${125.0*total_hours:.2f}")


from .plot import TimesheetPlotter


def create_data_file(path):
    path = append_filename_to_path(path)
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    if not os.path.exists(path):
        try:
            f = open(path, "a")
            empty_content = '''
            {
                "projects": []
            }
            '''
            f.write(empty_content.strip())
            f.close()
        except OSError:
            print(f"Failed creating {path}")
        else:
            print(f"{path} created!")
            return path
    else:
        print(f"{path} found!")
        return path


def is_dir(path):
    """Returns True if path has no extension."""
    return len(os.path.basename(path).split('.')) == 1


def is_valid_path(path):
    """Returns True if `path` is a directory or if has .json extension."""
    return is_dir(path) or os.path.basename(path).endswith('.json')


def append_filename_to_path(path, default_name="data.json"):
    if is_dir(path):
        path = path if not path.endswith('/') else path[:-1]
        return f"{path}/{default_name}"
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="project name")
    parser.add_argument(
        "-p",
        "--path",
        help="Path to the JSON data file",
        default="data.json"
    )
    parser.add_argument(
        "-r",
        "--report",
        help="Calculate and display a report of the time spent in the project",
        action="store_true"
    )
    parser.add_argument(
        "-d",
        "--daily-report",
        help="Generate a daily report of hours worked per day in the project",
        action="store_true"
    )
    parser.add_argument(
        "-P",
        "--plot",
        help="Graph the time spent in the project",
        action="store_true",
    )
    args = parser.parse_args()
    project = args.project
    path = args.path
    report = args.report
    daily_report = args.daily_report
    plot = args.plot

    if project and is_valid_path(path):
        path = create_data_file(path)
        tracker = Cinner(path)

        if report:
            tracker.print_total_report(project)
        elif daily_report or plot:
            tracker.print_daily_report(project)
            if plot:
                plotter = TimesheetPlotter(path, project)
                plotter.plot_daily_totals()
        else:
            tracker.add_or_update_project(project)

    else:
        print("Project or path not valid")


if __name__ == '__main__':
    main()
