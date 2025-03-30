#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import argparse
import json
import getpass
import requests
import sys
from pathlib import Path
from .time_tracker import TimeTracker
from .timesheet_plotter import TimesheetPlotter
from .redis_backend import RedisBackend

__all__ = ["TimeTracker", "TimesheetPlotter", "RedisBackend"]

# Default server URL
DEFAULT_SERVER_URL = "http://localhost:5002"

# Config file for storing API token and server URL
CONFIG_DIR = os.path.expanduser("~/.presis")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def get_config():
    """Get the configuration from the config file"""
    if not os.path.exists(CONFIG_FILE):
        return {"server_url": DEFAULT_SERVER_URL, "token": None}
    
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading config file: {e}")
        return {"server_url": DEFAULT_SERVER_URL, "token": None}

def save_config(config):
    """Save the configuration to the config file"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        print(f"Error saving config file: {e}")

def authenticate(config):
    """Authenticate with the server and get an API token"""
    print("Authentication required")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    
    try:
        response = requests.post(
            f"{config['server_url']}/api/auth",
            json={"email": email, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            config["token"] = data["token"]
            save_config(config)
            print("Authentication successful!")
            return True
        else:
            error = response.json().get("error", "Unknown error")
            print(f"Authentication failed: {error}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        print("You can still work offline, but changes won't sync to the server.")
        return False

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


def sync_with_server(config, tracker, project_name=None):
    """Sync data with the server"""
    if not config["token"]:
        print("Not authenticated. Use --login to authenticate first.")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {config['token']}"}
        
        # Sync data by sending local data and receiving server data
        response = requests.post(
            f"{config['server_url']}/api/sync",
            headers=headers,
            json={"projects": tracker.projects},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            # Get server data
            server_data = data["data"]
            
            # TODO: Update local data with merged result
            # For now we just show a message
            print("Data synced with server.")
            return True
        else:
            error = response.json().get("error", "Unknown error")
            print(f"Sync failed: {error}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        print("Working in offline mode. Changes will only be saved locally.")
        return False

def toggle_project_tracking(config, tracker, project_name, comment=None):
    """Toggle project tracking, using the API if available, or local file otherwise"""
    # Try to use the API if authenticated
    if config["token"]:
        try:
            headers = {"Authorization": f"Bearer {config['token']}"}
            data = {"comment": comment} if comment else {}
            
            response = requests.post(
                f"{config['server_url']}/api/projects/{project_name}/toggle",
                headers=headers,
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(data["message"])
                # Update local data by syncing
                sync_with_server(config, tracker)
                return True
            else:
                error = response.json().get("error", "Unknown error")
                print(f"API error: {error}")
                print("Falling back to local mode...")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")
            print("Falling back to local mode...")
    
    # Fall back to local mode if API fails or not authenticated
    tracker.add_or_update_project(project_name, comment)
    # Print status based on project state
    project = tracker.get_project(project_name)
    last_session = project['sessions'][-1]
    if last_session['end'] is None:
        print(f"Started time tracking for '{project_name}'")
    else:
        print(f"Stopped time tracking for '{project_name}'")
    return True

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Time tracking CLI")
    parser.add_argument(
        "project", 
        nargs="?", 
        help="project name"
    )
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
    parser.add_argument(
        "--login",
        help="Authenticate with the time tracking server",
        action="store_true"
    )
    parser.add_argument(
        "--set-server",
        help="Set the server URL",
        type=str
    )
    parser.add_argument(
        "--sync",
        help="Sync data with the server",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Get configuration
    config = get_config()
    
    # Handle server URL setting
    if args.set_server:
        config["server_url"] = args.set_server
        save_config(config)
        print(f"Server URL set to {args.set_server}")
        return
    
    # Handle authentication
    if args.login:
        authenticate(config)
        return
    
    # Prepare the tracker
    if is_valid_path(args.path):
        path = create_data_file(args.path)
        tracker = TimeTracker(path)
    else:
        print("Path not valid")
        return
    
    # Handle sync
    if args.sync:
        if args.project:
            sync_with_server(config, tracker, args.project)
        else:
            sync_with_server(config, tracker)
        return
    
    # Require project for other operations
    if not args.project:
        parser.print_help()
        print("\nError: project name is required unless using --login, --set-server, or --sync")
        return
    
    # Execute the command based on arguments
    if args.report:
        tracker.print_total_report(args.project)
    elif args.daily_report or args.plot:
        tracker.print_daily_report(args.project)
        if args.plot:
            plotter = TimesheetPlotter(tracker, args.project)
            plotter.plot_daily_totals()
    else:
        # Toggle project tracking
        toggle_project_tracking(config, tracker, args.project, args.comment)


if __name__ == '__main__':
    main()
