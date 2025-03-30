import json
from datetime import datetime, timedelta
from collections import defaultdict
from presis.redis_backend import RedisBackend

class RedisTimeTracker:
    """Redis-based implementation of TimeTracker that stores data in Redis instead of the filesystem"""
    
    def __init__(self, user_id, redis_backend):
        self.user_id = user_id
        self.redis = redis_backend
        self._projects = None  # Cache projects in memory
        
    @property
    def projects(self):
        """Get all projects for this user from Redis"""
        if self._projects is None:
            # Get all projects for this user
            raw_data = self.redis.r.get(f"timesheet:user:{self.user_id}")
            if raw_data:
                data = json.loads(raw_data)
                self._projects = data.get("projects", [])
            else:
                self._projects = []
        return self._projects
        
    def save_data(self):
        """Save the projects data to Redis"""
        self.redis.r.set(f"timesheet:user:{self.user_id}", json.dumps({"projects": self._projects}))
        
    def new_session(self, comment=None):
        """Creates a new working session dictionary with an optional comment."""
        tm = self.current_timestamp()
        if comment is None:
            comment = ""
        return {"start": tm, "end": None, "comment": comment}

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
            self.projects.append(project)
        else:
            last_session = project["sessions"][-1]
            if last_session["end"] is None:
                last_session["end"] = self.current_timestamp()
                if comment is None:
                    comment = ""
                last_session["closing_comment"] = comment
            else:
                project["sessions"].append(self.new_session(comment))
        self.save_data()
        
    def format_timestamp(self, date_str, time_str):
        """Formats date and time strings into the timestamp format used by the application."""
        # Convert from YYYY-MM-DD to DD/MM/YY
        date_parts = date_str.split('-')
        formatted_date = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0][2:]}"
        return f"{formatted_date} - {time_str}"
        
    def add_manual_session(self, project_name, start_date, start_time, end_date, end_time, comment, closing_comment=None):
        """Adds a manual session with specified start and end times."""
        project = self.get_project(project_name)
        if not project:
            project = {"project_name": project_name, "sessions": []}
            self.projects.append(project)
            
        start_timestamp = self.format_timestamp(start_date, start_time)
        end_timestamp = self.format_timestamp(end_date, end_time)
        
        new_session = {
            "start": start_timestamp,
            "end": end_timestamp,
            "comment": comment,
        }
        
        if closing_comment:
            new_session["closing_comment"] = closing_comment
            
        project["sessions"].append(new_session)
        self.save_data()
        
    def update_project_raw(self, project_name, project_data):
        """Update a project with raw data (used for syncing)"""
        project = self.get_project(project_name)
        if project:
            # Find the index of the project in the list
            index = next((i for i, p in enumerate(self.projects) if p["project_name"] == project_name), None)
            if index is not None:
                # Replace the project with the updated data
                self.projects[index] = project_data
                self.save_data()
                return True
        return False
        
    def merge_projects(self, source_project_name, destination_project_name):
        """Merge sessions from source project into destination project and then delete the source project"""
        source_project = self.get_project(source_project_name)
        destination_project = self.get_project(destination_project_name)
        
        # Validate that both projects exist
        if not source_project or not destination_project:
            return False, "Both source and destination projects must exist"
            
        # Don't merge a project with itself
        if source_project_name == destination_project_name:
            return False, "Cannot merge a project with itself"
        
        # Get all sessions from source project
        source_sessions = source_project.get("sessions", [])
        
        # Add each session from source to destination
        # Create a dictionary of existing sessions to avoid duplicates
        existing_sessions = {
            f"{s.get('start')}_{s.get('end')}": True 
            for s in destination_project['sessions']
        }
        
        # Add non-duplicate sessions from source to destination
        for session in source_sessions:
            session_key = f"{session.get('start')}_{session.get('end')}"
            if session_key not in existing_sessions:
                destination_project['sessions'].append(session)
                
        # Sort sessions by start time
        destination_project['sessions'].sort(
            key=lambda x: x.get('start', ''))
        
        # Remove the source project
        self.projects = [p for p in self.projects if p["project_name"] != source_project_name]
        
        # Save changes
        self.save_data()
        
        return True, f"Successfully merged {source_project_name} into {destination_project_name}"
    
    def add_project_raw(self, project_data):
        """Add a project from raw data (used for syncing)"""
        project_name = project_data.get("project_name")
        if not project_name:
            return False
            
        # Check if project already exists
        existing_project = self.get_project(project_name)
        if existing_project:
            return self.update_project_raw(project_name, project_data)
            
        # Add the new project
        self.projects.append(project_data)
        self.save_data()
        return True

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
