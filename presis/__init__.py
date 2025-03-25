#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import argparse
from .time_tracker import TimeTracker
from .timesheet_plotter import TimesheetPlotter
from .redis_backend import RedisBackend

__all__ = ["TimeTracker", "TimesheetPlotter", "RedisBackend"]


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
        # print(f"{path} found!")
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
    parser.add_argument(
        "-c",
        "--comment",
        help="Comment for creating or closing a time entry",
        type=str
    )
    args = parser.parse_args()
    project = args.project
    path = args.path
    report = args.report
    daily_report = args.daily_report
    plot = args.plot
    comment = args.comment

    if project and is_valid_path(path):
        path = create_data_file(path)
        tracker = TimeTracker(path)

        if report:
            tracker.print_total_report(project)
        elif daily_report or plot:
            tracker.print_daily_report(project)
            if plot:
                plotter = TimesheetPlotter(tracker, project)
                plotter.plot_daily_totals()
        else:
            tracker.add_or_update_project(project, comment)

    else:
        print("Project or path not valid")


if __name__ == '__main__':
    main()
