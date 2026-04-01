"""Application state machine for FridgeFit."""

import time

from .auth import UserManager
from .meal_planner import generate_ai_meal_plan


class FridgeFitApp:
    """
    The main application controller.
    Manages the state machine logic for navigating through different menus.
    """

    def __init__(self):
        """Initialize the core components and application state."""
        self.user_manager = UserManager()
        self.current_user = None
        self.current_state = "main_menu"

    def show_main_menu(self) -> str:
        """Display the landing page and return the next state."""
        print("==============================")
        print("   WELCOME TO FRIDGEFIT")
        print("==============================")
        print("1. Log In")
        print("2. Register")
        print("3. Exit")
        print("==============================")

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            return "login"
        if choice == "2":
            return "register"
        if choice == "3":
            return "exit"

        print("\nInvalid choice. Please select 1, 2, or 3.")
        time.sleep(1.5)
        return "main_menu"

    def show_dashboard(self) -> str:
        """Display the dashboard for an authenticated user."""
        while True:
            print("\n==============================")
            print("      FRIDGEFIT DASHBOARD")
            print(f"      User: {self.current_user}")
            print("==============================")
            print("1. Generate Personalized AI Recipe")
            print("2. Log Out")
            print("==============================")

            choice = input("Select an option (1-2): ").strip()

            if choice == "1":
                generate_ai_meal_plan(self.current_user)
            elif choice == "2":
                print("Logging out...")
                time.sleep(1)
                self.current_user = None
                return "main_menu"
            else:
                print("Invalid choice. Please try again.")

    def run(self) -> None:
        """Run the application until the user exits."""
        while self.current_state != "exit":
            if self.current_state == "main_menu":
                self.current_state = self.show_main_menu()
            elif self.current_state == "login":
                logged_in_user = self.user_manager.login()
                if logged_in_user:
                    self.current_user = logged_in_user
                    self.current_state = "logged_in_dashboard"
                else:
                    self.current_state = "main_menu"
            elif self.current_state == "register":
                self.current_state = self.user_manager.register()
            elif self.current_state == "logged_in_dashboard":
                self.current_state = self.show_dashboard()

        print("\nGoodbye! Keep fit and eat well!")


def main() -> None:
    """Application entry point."""
    app = FridgeFitApp()
    app.run()
