"""
FridgeFit: AI-Powered Dynamic Meal Planner
==========================================
Course Project for INT2067 02E
Wang Zejia11598856, You Xuanhe11592644
"""

import tkinter as tk
from tkinter import filedialog
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import zipfile
import lxml.etree as ET
import csv
import os
import json
import time
from openai import OpenAI 

# -------------------------------- 1.  Transform the Apple Health Data from XML to CSV (You Xuanhe)  --------------------------------

def process_apple_health_zip():
    print("Apple Health Export Tool (Output to Project Folder)")
    project_folder = Path(__file__).parent.absolute()

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(title="Choose Apple Health export.zip", filetypes=[("ZIP files", "*.zip")])
    root.destroy()

    if not file_path: return

    zip_path = Path(file_path)
    output_folder = project_folder / zip_path.stem
    if not output_folder.exists():
        os.makedirs(output_folder)
        print(f"Created directory in project: {output_folder}")

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            xml_files = [f for f in z.namelist() if f.endswith('.xml')]

            for xml_name in xml_files:
                if "cda" in xml_name.lower():
                    continue

                file_info = z.getinfo(xml_name)
                total_size = file_info.file_size
                print(f"Analyzing {xml_name}... Please wait.")
                total_records = 0
                with z.open(xml_name) as f_scan:
                    for event, elem in ET.iterparse(f_scan, events=('end',)):
                        if elem.tag in ('Record', 'Workout', 'ActivitySummary'):
                            total_records += 1
                        elem.clear()
                if total_records == 0:
                    print(f"No health record found in {xml_name}, skipping.")
                    continue
                print(f"Total entries found: {total_records:,}")

                target_tags = ('Record', 'Workout', 'ActivitySummary')
                outputs = {}
                writers = {}

                with z.open(xml_name) as f:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc="Converting", colour="cyan") as pbar:
                        context = ET.iterparse(f, events=('end',), tag=target_tags)
                        count = 0
                        for event, elem in context:
                            tag_name = elem.tag
                            data = dict(elem.attrib)

                            if data:
                                if tag_name not in outputs:
                                    csv_name = output_folder / f"{tag_name}.csv"
                                    f_out = open(csv_name, 'w', newline='', encoding='utf-8-sig')

                                    writer = csv.DictWriter(f_out, fieldnames=data.keys(), extrasaction='ignore')
                                    writer.writeheader()
                                    outputs[tag_name] = f_out
                                    writers[tag_name] = writer

                                writers[tag_name].writerow(data)
                                count += 1

                            pbar.update(f.tell() - pbar.n)
                            elem.clear()
                            while elem.getprevious() is not None:
                                del elem.getparent()[0]

                for f_out in outputs.values():
                    f_out.close()

                if count > 0:
                    print(f"Success: Generated {len(outputs)} files in /{output_folder.name}/")

        print(f"\nDone! Files are located in: {output_folder}")
        return output_folder

    except Exception as e:
        print(f"\nError: {e}")
        return None

# -------------------------------- 1.  Read the CSV file and return health data (Wang Zejia) --------------------------------

def get_health_data_summary(folder_path):
    try:
        folder_path = Path(folder_path)
        record_file = folder_path / "Record.csv"

        if not record_file.exists():
            return None

        print(f"\n[System] Analyzing health data... This might take a few seconds.")
        # Load specific columns to save memory
        df = pd.read_csv(record_file, usecols=['type', 'startDate', 'value'], dtype=str)

        # Filter and clean Step Count data
        df_steps = df[df['type'] == 'HKQuantityTypeIdentifierStepCount'].copy()
        df_steps['startDate'] = pd.to_datetime(df_steps['startDate'], errors='coerce')
        df_steps['value'] = pd.to_numeric(df_steps['value'], errors='coerce')

        # Filter and clean Active Energy Burned data
        df_energy = df[df['type'] == 'HKQuantityTypeIdentifierActiveEnergyBurned'].copy()
        df_energy['startDate'] = pd.to_datetime(df_energy['startDate'], errors='coerce')
        df_energy['value'] = pd.to_numeric(df_energy['value'], errors='coerce')

        if not df_steps.empty:
            # Get the most recent date in the dataset
            latest_date = df_steps['startDate'].dt.date.max()

            # Sum up values for the latest date
            total_steps = df_steps[df_steps['startDate'].dt.date == latest_date]['value'].sum()
            total_energy = 0
            if not df_energy.empty:
                total_energy = df_energy[df_energy['startDate'].dt.date == latest_date]['value'].sum()

            summary = f"Recorded Date: {latest_date}, Total Steps: {int(total_steps)}, Active Energy Burned: {int(total_energy)} kcal"
            return summary
        else:
            return "No valid step data found in records."

    except Exception as e:
        print(f"[Warning] Could not parse health data cleanly: {e}")
        return None

# -------------------------------- 2.  AI meal plan manu system (Wang Zejia) --------------------------------

def generate_ai_meal_plan(username):
    print("\n==============================")
    print("     AI MEAL PLAN GENERATOR")
    print("==============================")

    # 1. Collect User Goals
    print("Please select your primary fitness goal:")
    print("1. Weight Loss")
    print("2. Muscle Gain")
    print("3. Maintenance")

    goal = "Maintenance"
    while True:
        choice = input("Select an option (1-3): ").strip()
        if choice == '1':
            goal = "Weight Loss"
            break
        elif choice == '2':
            goal = "Muscle Gain"
            break
        elif choice == '3':
            goal = "Maintenance"
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    # 2. Collect Available Ingredients
    ingredients = input("\nWhat ingredients are in your fridge right now? (eg. 1kg pork, 4 eggs): ").strip()

    # 3. Integrate Apple Health Data or Manual Input
    print("\n[Apple Health Integration]")
    print("Would you like to import your Apple Health data for precise dynamic meal adjustment?")
    print("💡 Tip: Go to the 'Health' app on your iPhone > Profile (top right) > 'Export All Health Data'.")
    use_health_data = input("Import your export.zip now? (y/n): ").strip().lower()

    activity_level = ""
    if use_health_data == 'y':
        print("\n[System] Please select your Apple Health export.zip file in the popup window...")
        time.sleep(1)
        output_folder = process_apple_health_zip()

        if output_folder:
            health_summary = get_health_data_summary(output_folder)
            if health_summary:
                print(f"[System] Success! Extracted data: {health_summary}")
                activity_level = f"User's precise Apple Health data for the day: {health_summary}"
            else:
                print("[System] Data parsing failed. Reverting to manual input.")
                activity_level = input(
                    "Please manually enter today's workout (e.g., 'ran 10km', 'sedentary'): ").strip()
        else:
            print("[System] No file selected. Reverting to manual input.")
            activity_level = input("Please manually enter today's workout (e.g., 'ran 10km', 'sedentary'): ").strip()
    else:
        activity_level = input("\nPlease manually enter today's workout (e.g., 'ran 10km', 'sedentary'): ").strip()

    # -------------------------------- 2.  DeepSeek API (You Xuanhe) --------------------------------

    # 4. API Invocation
    print("\n[AI] Synthesizing data via DeepSeek API... Please wait.")

    # Get DeepSeek API Key From Environment Variables or User Input
    API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not API_KEY:
        API_KEY = input("\n⚠️ DEEPSEEK_API_KEY not found. Please paste your DeepSeek API Key here: ").strip()
        print("Thinking...")

    if not API_KEY:
        print("\n[Error] API Key is required. Returning to Dashboard...")
        time.sleep(2)
        return
    # -------------------------------- 3.  Prompt sent to LLM API (Wang Zejia) --------------------------------

    # Construct the prompt for the LLM
    prompt = f"""
    You are an expert sports nutritionist and master chef for the app FridgeFit.
    User Data:
    - Available Ingredients: {ingredients}
    - Primary Fitness Goal: {goal}
    - Today's Energy Expenditure: {activity_level}

    Please provide a personalized recipe adjusting macros/calories based on their exact energy expenditure today. Include cooking instructions and briefly explain why this fits their goal and activity level. Use markdown.
    """

    # -------------------------------- 3.  Call LLM API (You Xuanhe) --------------------------------

    try:
        # Initialize OpenAI and point tp DeepSeek 
        client = OpenAI(
            api_key=API_KEY,
            base_url="https://api.deepseek.com" # Deepseek API
        )

        # Use DeepSeek V3
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[
                {"role": "system", "content": "You are a helpful and professional health assistant."},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )

        print("\n" + "=" * 50)
        print("🍽️ YOUR PERSONALIZED AI RECIPE 🍽️")
        print("=" * 50)
        # Get respond
        print(response.choices[0].message.content) 
        print("=" * 50)

    except Exception as e:
        print(f"\n[Error] DeepSeek API connection failed: {e}")
        print("Hint: Please ensure your API Key is correct and you have internet access.")

    input("\n(Press Enter to return to Dashboard)")

# -------------------------------- 4.  Main menu system (Wang Zejia)  --------------------------------

class UserManager:
    """
    Handles user authentication, registration, and persistent data storage.
    Data is stored locally in a JSON file to maintain state between sessions.
    """

    def __init__(self, db_file="users.json"):
        """
        Initializes the UserManager.

        Args:
            db_file (str): The filename used for storing user credentials.
        """
        self.db_file = db_file
        self.users_dict = self.load_users()

    def load_users(self):
        """
        Loads the user dictionary from the local JSON file.
        Creates a default admin account if the file does not exist.

        Returns:
            dict: A dictionary mapping usernames to passwords.
        """
        if not os.path.exists(self.db_file):
            default_users = {"admin": "123"}
            with open(self.db_file, "w") as file:
                json.dump(default_users, file)
            return default_users

        with open(self.db_file, "r") as file:
            return json.load(file)

    def save_users(self):
        """Saves the current user dictionary to the local JSON file."""
        with open(self.db_file, "w") as file:
            json.dump(self.users_dict, file)

    def register(self):
        """
        Handles the user registration flow.
        Validates username uniqueness and password length criteria.

        Returns:
            str: The next application state ('login' on success, 'register' on retry).
        """
        print("==============================")
        print("     FRIDGEFIT - REGISTER")
        print("==============================")

        username = input("Please enter your username: ").strip()

        if username in self.users_dict:
            print("\nThat username is already taken. Please try another one.")
            time.sleep(2)
            return 'register'

        password = input("Please enter an 8-character password: ").strip()

        if len(password) < 8:
            print("\nPassword must be at least 8 characters long! Try again.")
            time.sleep(2)
            return 'register'

        # Store new user and update database
        self.users_dict[username] = password
        self.save_users()

        print("\nRegistration successful! Redirecting to login page...")
        time.sleep(2)
        return 'login'

    def login(self):
        """
        Handles the user login flow and authentication.
        Includes a hidden bypass feature for administrators.

        Returns:
            str or None: The authenticated username if successful, None otherwise.
        """
        print("==============================")
        print("       FRIDGEFIT - LOGIN")
        print("==============================")

        username = input("Username: ").strip()

        # Administrator Bypass Check
        if username.lower() == 'admin':
            print("\n[System] Admin bypass triggered! Welcome back, Boss.")
            time.sleep(1)
            return 'admin'

        password = input("Password: ").strip()

        # Validate credentials
        if username not in self.users_dict:
            print("\nAccount not found! Returning to Main Menu...")
            time.sleep(1.5)
            return None
        elif self.users_dict[username] == password:
            print(f"\nLogin successful! Welcome to FridgeFit, {username}.")
            time.sleep(1.5)
            return username
        else:
            print("\nIncorrect password! Returning to Main Menu...")
            time.sleep(1.5)
            return None


class FridgeFitApp:
    """
    The main application controller.
    Manages the state machine logic for navigating through different menus.
    """

    def __init__(self):
        """Initializes the core components and application state."""
        self.user_manager = UserManager()
        self.current_user = None
        self.current_state = 'main_menu'

    def show_main_menu(self):
        """
        Displays the landing page of the application.

        Returns:
            str: The next state based on user selection.
        """
        print("==============================")
        print("   WELCOME TO FRIDGEFIT")
        print("==============================")
        print("1. Log In")
        print("2. Register")
        print("3. Exit")
        print("==============================")

        choice = input("Select an option (1-3): ").strip()

        if choice == '1':
            return 'login'
        elif choice == '2':
            return 'register'
        elif choice == '3':
            return 'exit'
        else:
            print("\nInvalid choice. Please select 1, 2, or 3.")
            time.sleep(1.5)
            return 'main_menu'

    def show_dashboard(self):
        """
        Displays the dashboard available to authenticated users.
        Handles the invocation of core features (Meal generation) or logging out.

        Returns:
            str: The 'main_menu' state when the user decides to log out.
        """
        while True:
            print("\n==============================")
            print(f"      FRIDGEFIT DASHBOARD")
            print(f"      User: {self.current_user}")
            print("==============================")
            print("1. Generate Personalized AI Recipe")
            print("2. Log Out")
            print("==============================")

            choice = input("Select an option (1-2): ").strip()

            if choice == '1':
                # Trigger the primary business logic
                generate_ai_meal_plan(self.current_user)
            elif choice == '2':
                print("Logging out...")
                time.sleep(1)
                self.current_user = None
                return 'main_menu'
            else:
                print("Invalid choice. Please try again.")

    def run(self):
        """
        The main event loop driving the application state machine.
        Continues running until the state changes to 'exit'.
        """
        while self.current_state != 'exit':
            if self.current_state == 'main_menu':
                self.current_state = self.show_main_menu()

            elif self.current_state == 'login':
                logged_in_user = self.user_manager.login()
                if logged_in_user:
                    self.current_user = logged_in_user
                    self.current_state = 'logged_in_dashboard'
                else:
                    self.current_state = 'main_menu'

            elif self.current_state == 'register':
                self.current_state = self.user_manager.register()

            elif self.current_state == 'logged_in_dashboard':
                self.current_state = self.show_dashboard()

        print("\nGoodbye! Keep fit and eat well!")


if __name__ == "__main__":
    app = FridgeFitApp()
    app.run()