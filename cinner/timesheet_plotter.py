import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
from datetime import datetime
from . import Cinner


class TimesheetPlotter:
    def __init__(self, json_file, project):
        self.tracker = Cinner(json_file)
        self.project = project

    def plot_daily_totals(self):
        """Scatter plot the summed hours per day with days of the month on x-axis and hours worked on y-axis."""
        daily_totals = self.tracker.assemble_total_hours_per_day(self.project)
        daily_hours = defaultdict(float)

        for date, total_time in daily_totals:
            daily_hours[date] = total_time.total_seconds() / 3600.0

        days = sorted(daily_hours.keys())
        total_hours = [daily_hours[day] for day in days]
        total_sum = sum(total_hours)

        plt.figure(figsize=(12, 6))
        plt.scatter(days, total_hours, color="blue", alpha=0.7)

        # Add annotations to each plot mark
        for day, hours in zip(days, total_hours):
            plt.text(day, hours, f"{hours:.1f}", fontsize=9, ha="right", va="bottom", color="red")

        # Format x-axis with readable date labels
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        plt.xlabel("Date")
        plt.ylabel("Total Hours Worked")
        plt.title(f"Total Hours Worked per Day - Project: {self.project}", pad=20)
        plt.grid(True)

        # Increase space above the title
        plt.subplots_adjust(left=0.15, right=0.85, bottom=0.15, top=0.85)

        # Print the total sum on the plot
        plt.text(
            0.95,
            0.95,
            f"Total Hours: {total_sum:.2f}",
            fontsize=12,
            ha="right",
            va="top",
            transform=plt.gca().transAxes,
            color="green",
        )
        plt.show()
