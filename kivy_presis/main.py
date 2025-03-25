from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from presis import TimeTracker, RedisBackend, TimesheetPlotter
from kivy_presis.auth.jwt_utils import JwtUtils

class LoginForm(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.redis_backend = RedisBackend()

    def login(self, username, password):
        """Authenticate the user against Redis."""
        if self.redis_backend.authenticate_user(username, password):
            app = App.get_running_app()
            app.username = username
            app.switch_to_main_screen()
        else:
            self.show_popup("Login Failed", "Invalid username or password.")

    def register(self, username, password):
        """Register a new user in Redis."""
        self.redis_backend.create_user(username, password)
        self.show_popup("Registration Successful", "User registered successfully.")

    def show_popup(self, title, message):
        """Display a popup message."""
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))
        close_button = Button(text="Close", size_hint_y=None, height=40)
        content.add_widget(close_button)
        popup = Popup(title=title, content=content, size_hint=(None, None), size=(400, 200))
        close_button.bind(on_release=popup.dismiss)
        popup.open()

class TimesheetScreen(BoxLayout):
    username = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.redis_backend = RedisBackend()

    def save_timesheet(self, project_name):
        """Save the timesheet to Redis."""
        tracker = TimeTracker("timesheet.json")
        tracker.save_data()
        data = tracker.load_data("timesheet.json")
        self.redis_backend.save_timesheet(self.username, project_name, data)

    def load_timesheet(self, project_name):
        """Load the timesheet from Redis."""
        data = self.redis_backend.load_timesheet(self.username, project_name)
        if data:
            tracker = TimeTracker("timesheet.json")
            tracker.projects = data.get("projects", [])
            tracker.save_data()

    def generate_scoped_token(self, project_name):
        """Generate a read-only scoped token for sharing timesheets."""
        user_id = self.redis_backend.get_user_id(self.username)
        token = JwtUtils.encode_token(user_id, project_name, scope="readonly", expires_in=24)
        self.show_popup("Token Generated", f"Token for project {project_name}: {token}")

    def show_popup(self, title, message):
        """Display a popup message."""
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))
        close_button = Button(text="Close", size_hint_y=None, height=40)
        content.add_widget(close_button)
        popup = Popup(title=title, content=content, size_hint=(None, None), size=(400, 200))
        close_button.bind(on_release=popup.dismiss)
        popup.open()

class PresisApp(App):
    username = StringProperty("")

    def build(self):
        return LoginForm()

    def switch_to_main_screen(self):
        """Switch to the timesheet screen after successful login."""
        self.root.clear_widgets()
        self.root.add_widget(TimesheetScreen(username=self.username))


if __name__ == "__main__":
    PresisApp().run()
