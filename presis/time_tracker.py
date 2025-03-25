
import os
import json
from datetime import datetime, timedelta
from functools import reduce
from collections import defaultdict


class TimeTracker:
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

    def new_session(self, comment=None):
        """Creates a new working session dictionary with an optional comment."""
        tm = self.current_timestamp()
        print(f'starting new session at: {tm}')
        if comment is None:
            comment = input("Enter a comment for this new session: ")
        return { "start": tm, "end": None, "comment": comment }

    def current_timestamp(self):
        """Returns the current timestamp with a specific format."""
        return datetime.now().strftime("%d/%m/%y - %H:%M:%S")

    def get_project(self, project_name):
        """Finds a specific project in the projects list."""
        return next((p for p in self.projects if p["project_name"] == project_name), None)

    def add_or_update_project(self, project_name, comment=None):
        """Creates a new project or adds a timestamp to an existing one with comments."""
        project = self.get_project(project_name)
        if not project:
            project = {"project_name": project_name, "sessions": [self.new_session(comment)]}
            print(f'creating project {project_name}')
            self.projects.append(project)
        else:
            last_session = project["sessions"][-1]
            if last_session["end"] is None:
                last_session["end"] = self.current_timestamp()
                if comment is None:
                    comment = input("Enter a closing comment for this session: ")
                last_session["closing_comment"] = comment
                print(f'ended session at: {last_session["end"]}')
            else:
                project["sessions"].append(self.new_session(comment))
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
