"""User authentication and persistence."""

import json
import time
from pathlib import Path
from typing import Union

from .config import DEFAULT_USERS, USERS_DB_FILE


class UserManager:
    """
    Handles user authentication, registration, and persistent data storage.
    Data is stored locally in a JSON file to maintain state between sessions.
    """

    def __init__(self, db_file: Union[str, Path] = USERS_DB_FILE):
        """Initialize the user manager and load persisted users."""
        self.db_file = Path(db_file)
        self.users_dict = self.load_users()

    def load_users(self):
        """
        Load the user dictionary from disk.
        Creates a default admin account if the file does not exist.
        """
        if not self.db_file.exists():
            with self.db_file.open("w", encoding="utf-8") as file:
                json.dump(DEFAULT_USERS, file)
            return DEFAULT_USERS.copy()

        with self.db_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save_users(self) -> None:
        """Persist the current user dictionary to disk."""
        with self.db_file.open("w", encoding="utf-8") as file:
            json.dump(self.users_dict, file)

    def register(self) -> str:
        """
        Handle the user registration flow.
        Returns the next application state.
        """
        print("==============================")
        print("     FRIDGEFIT - REGISTER")
        print("==============================")

        username = input("Please enter your username: ").strip()

        if username in self.users_dict:
            print("\nThat username is already taken. Please try another one.")
            time.sleep(2)
            return "register"

        password = input("Please enter an 8-character password: ").strip()

        if len(password) < 8:
            print("\nPassword must be at least 8 characters long! Try again.")
            time.sleep(2)
            return "register"

        self.users_dict[username] = password
        self.save_users()

        print("\nRegistration successful! Redirecting to login page...")
        time.sleep(2)
        return "login"

    def login(self):
        """
        Handle the user login flow and authentication.
        Includes a hidden bypass feature for administrators.
        """
        print("==============================")
        print("       FRIDGEFIT - LOGIN")
        print("==============================")

        username = input("Username: ").strip()

        if username.lower() == "admin":
            print("\n[System] Admin bypass triggered! Welcome back, Boss.")
            time.sleep(1)
            return "admin"

        password = input("Password: ").strip()

        if username not in self.users_dict:
            print("\nAccount not found! Returning to Main Menu...")
            time.sleep(1.5)
            return None
        if self.users_dict[username] == password:
            print(f"\nLogin successful! Welcome to FridgeFit, {username}.")
            time.sleep(1.5)
            return username

        print("\nIncorrect password! Returning to Main Menu...")
        time.sleep(1.5)
        return None
