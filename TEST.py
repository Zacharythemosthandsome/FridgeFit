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

# -------------------------------- 1.  Menu and login system (Wang Zejia)  --------------------------------
# Store user dictionary through a text file
DB_FILE = "users.json"

# Define a function to load users from the JSON file.
def load_users():
    # If the file doesn't exist yet, make one with an admin account.
    if not os.path.exists(DB_FILE):
        default_users = {"admin":"123"}
        with open(DB_FILE, "w") as file:
            json.dump(default_users, file)
        return default_users

    # If the file exists, read it and return the dictionary
    with open(DB_FILE, "r") as file:
        return json.load(file)

# Define a function to save the user dictionary back to the JSON file.
def save_users(users_dict):
    with open(DB_FILE, "w") as file:
        json.dump(users_dict, file)

# Define a function to show and operate the main menu.
def main_menu():
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

# Define a function to handle new user registration.
def register_view(users_dict):
    print("==============================")
    print("     FRIDGEFIT - REGISTER")
    print("==============================")

    username = input("Please enter your username: ").strip()

    # Check if username already exists
    if username in users_dict:
        print("\nThat username is already taken. Please try another one.")
        time.sleep(2)
        return 'register'

    password = input("Please enter an 8-character password: ").strip()

    # Check password length
    if len(password) < 8:
        print("\nPassword must be at least 8 characters long! Try again.")
        time.sleep(2)
        return 'register'

    # Add the new user to our dictionary and save it
    users_dict[username] = password
    save_users(users_dict)

    print("\nRegistration successful! Redirecting to login page...")
    time.sleep(2)
    return 'login'

# Define a function to handle user login.
def login_view(users_dict):
    print("==============================")
    print("       FRIDGEFIT - LOGIN")
    print("==============================")

    username = input("Username: ").strip()
    password = input("Password: ").strip()

    # Check if the user exists in the dictionary
    if username not in users_dict:
        print("\nAccount not found! You need to register first.")
        print("Redirecting to the registration page...")
        time.sleep(2)
        return 'register'

    # Check if the password matches
    elif users_dict[username] == password:
        print(f"\nLogin successful! Welcome to FridgeFit, {username}.")
        time.sleep(2)
        return 'logged_in_dashboard'

    else:
        print("\nIncorrect password. Please try again.")
        time.sleep(2)
        return 'login'


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

# -------------------------------- 2.  Read the CSV file and return health data (Wang Zejia) --------------------------------

def get_health_data_summary(folder_path):
    try:
        folder_path = Path(folder_path)
        record_file = folder_path / "Record.csv"

        if not record_file.exists():
            return None

        print(f"\n[System] Analyzing health data... This might take a few seconds.")
        df = pd.read_csv(record_file, usecols=['type', 'startDate', 'value'], dtype=str)

        df_steps = df[df['type'] == 'HKQuantityTypeIdentifierStepCount'].copy()
        df_steps['startDate'] = pd.to_datetime(df_steps['startDate'], errors='coerce')
        df_steps['value'] = pd.to_numeric(df_steps['value'], errors='coerce')

        df_energy = df[df['type'] == 'HKQuantityTypeIdentifierActiveEnergyBurned'].copy()
        df_energy['startDate'] = pd.to_datetime(df_energy['startDate'], errors='coerce')
        df_energy['value'] = pd.to_numeric(df_energy['value'], errors='coerce')

        if not df_steps.empty:
            latest_date = df_steps['startDate'].dt.date.max()
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


def generate_ai_meal_plan(username):
    print("\n==============================")
    print("     AI MEAL PLAN GENERATOR")
    print("==============================")

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

    ingredients = input("\nWhat ingredients are in your fridge right now? (eg. 1kg pork, 4 eggs): ").strip()

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
    print("\n[AI] Synthesizing data via DeepSeek API... Please wait.")

    # Get DeepSeek API Key From Environment
    API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not API_KEY:
        API_KEY = input("\n⚠️ DEEPSEEK_API_KEY not found. Please paste your DeepSeek API Key here: ").strip()

    if not API_KEY:
        print("\n[Error] API Key is required. Returning to Dashboard...")
        time.sleep(2)
        return
    # -------------------------------- 3.  Prompt sent to LLM API (Wang Zejia) --------------------------------
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

# -------------------------------- 1.  Menu and login system (Wang Zejia)  --------------------------------

def logged_in_dashboard(username):
    while True:
        print("\n==============================")
        print(f"      FRIDGEFIT DASHBOARD")
        print(f"      User: {username}")
        print("==============================")
        print("1. Generate Personalized AI Recipe")
        print("2. Log Out")
        print("==============================")

        choice = input("Select an option (1-2): ").strip()

        if choice == '1':
            generate_ai_meal_plan(username)
        elif choice == '2':
            print("Logging out...")
            time.sleep(1)
            return 'main_menu'
        else:
            print("Invalid choice. Please try again.")

# -------------------------------- 4.  Program Execution and Loops (Wang Zejia)  --------------------------------
# Define a function to control the flow of this program.
def run_app():
    # Load users into a dictionary when this program starts
    users_dict = load_users()

    current_state = 'main_menu'
    current_user = None

    while current_state != 'exit':
        if current_state == 'main_menu':
            current_state = main_menu()

        elif current_state == 'login':
            print("\n==============================")
            print("       FRIDGEFIT - LOGIN")
            print("==============================")
            username = input("Username: ").strip()

            if username.lower() == 'admin':
                print("\n[System] Admin bypass triggered! Welcome back, Boss.")
                time.sleep(1)
                current_user = 'admin'
                current_state = 'logged_in_dashboard'
                continue

            password = input("Password: ").strip()

            if username not in users_dict:
                print("\nAccount not found! Returning to Main Menu...")
                time.sleep(1.5)
                current_state = 'main_menu'
            elif users_dict[username] == password:
                print(f"\nLogin successful! Welcome to FridgeFit, {username}.")
                time.sleep(1.5)
                current_user = username
                current_state = 'logged_in_dashboard'
            else:
                print("\nIncorrect password! Returning to Main Menu...")
                time.sleep(1.5)
                current_state = 'main_menu'

        elif current_state == 'register':
            current_state = register_view(users_dict)

        elif current_state == 'logged_in_dashboard':
            current_state = logged_in_dashboard(current_user)

    print("\nGoodbye! Keep fit and eat well!")


if __name__ == "__main__":
    run_app()