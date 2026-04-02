# FridgeFit

FridgeFit is a command-line nutrition assistant that combines fridge ingredients, a fitness goal, and either manual activity input or Apple Health export data to generate a personalized meal suggestion through the DeepSeek API.

## Features

- Local user registration and login backed by `users.json`
- Three meal-planning goals: Weight Loss, Muscle Gain, and Maintenance
- Optional Apple Health `export.zip` import through a file picker
- XML-to-CSV conversion for Apple Health `Record`, `Workout`, and `ActivitySummary` data
- Health summary extraction based on the latest recorded day
- AI recipe generation through the OpenAI SDK with the DeepSeek endpoint

## Requirements

- Python 3.8+
- Packages listed in `requirements.txt`
- A valid DeepSeek API key for recipe generation
- Internet access for DeepSeek requests
- An Apple Health `export.zip` file if you want to test the import workflow

## Installation


1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Provide your DeepSeek API key in one of these ways:

- Set `DEEPSEEK_API_KEY` in your environment before launching the app.
- Paste the key into the terminal when the program asks for it.

## Usage

Run the application from the same folder as `project.py`:

```bash
python project.py
```

Typical flow:

1. Register a user or log in.
2. Open the dashboard.
3. Choose `Generate Personalized AI Recipe`.
4. Select a goal, enter ingredients, and choose either Apple Health import or manual workout input.
5. Provide a DeepSeek API key if one is not already set.
6. Review the generated recipe, then press Enter to return to the dashboard.

## Apple Health Import Behavior

When you choose Apple Health import, the program:

1. Opens a file picker for an `export.zip` file.
2. Extracts XML records into CSV files inside a new folder beside `project.py`.
3. Reads `Record.csv`.
4. Summarizes the latest available day of:
   - `HKQuantityTypeIdentifierStepCount`
   - `HKQuantityTypeIdentifierActiveEnergyBurned`
5. Uses that summary in the AI prompt.

If you cancel the file picker or parsing fails, the app falls back to manual activity input.

## Project Structure

```text
.
├── .gitignore
├── LICENSE
├── README.md
├── fridgefit/
│   ├── app.py
│   ├── auth.py
│   ├── config.py
│   ├── health.py
│   └── meal_planner.py
├── project.py
└── requirements.txt
```

Generated at runtime:

- `users.json` is created in the project folder beside `project.py` if it does not already exist.
- An imported Apple Health zip creates a sibling folder named after the zip file, containing CSV output such as `Record.csv`.
- Python cache files inside `__pycache__/` are generated locally and should not be committed.

## Notes About Current Implementation

- New registrations require a password with at least 8 characters.
- On first run, the program creates a default `admin` entry in `users.json`.
- Entering `admin` at the login username prompt triggers a built-in admin bypass and opens the dashboard without checking a password.
- Apple Health exports can be large, so conversion may take some time.

## Manual Test Cases For `project.py`

Use these cases to test the main features of the application. For repeatable results, run the app from the `Final Project` folder and use a fresh username when needed.

### Test Case 1: Register a New User Successfully

Steps:

1. Run `python project.py`.
2. At the main menu, choose Register.
3. Enter a new username.
4. Enter a password with at least 8 characters.
5. Confirm that the app reports successful registration and returns to login.

Sample dialogue:

```text
Select an option (1-3): _2_
Please enter your username: _alice_
Please enter an 8-character password: _password1_
```

Expected result:

- The program prints `Registration successful! Redirecting to login page...`
- The username is saved to `users.json`.

### Test Case 2: Reject a Password That Is Too Short

Steps:

1. Start the program.
2. Choose Register.
3. Enter a new username.
4. Enter a password shorter than 8 characters.

Sample dialogue:

```text
Select an option (1-3): _2_
Please enter your username: _bob_
Please enter an 8-character password: _short_
```

Expected result:

- The program prints `Password must be at least 8 characters long! Try again.`
- The user is returned to the register flow.

### Test Case 3: Reject a Duplicate Username

Steps:

1. Register a username once.
2. Start the register flow again.
3. Re-enter the same username.

Sample dialogue:

```text
Select an option (1-3): _2_
Please enter your username: _alice_
```

Expected result:

- The program prints `That username is already taken. Please try another one.`
- No duplicate account is created.

### Test Case 4: Log In and Log Out as a Normal User

Steps:

1. Run the program.
2. Choose Log In.
3. Enter a valid registered username and password.
4. Confirm that the dashboard appears.
5. Choose Log Out.

Sample dialogue:

```text
Select an option (1-3): _1_
Username: _alice_
Password: _password1_
Select an option (1-2): _2_
```

Expected result:

- The program prints `Login successful! Welcome to FridgeFit, alice.`
- The dashboard shows `User: alice`.
- Choosing `2` logs the user out and returns to the main menu.

### Test Case 5: Verify the Admin Bypass

Steps:

1. Run the program.
2. Choose Log In.
3. Enter `admin` as the username.

Sample dialogue:

```text
Select an option (1-3): _1_
Username: _admin_
```

Expected result:

- The program prints `[System] Admin bypass triggered! Welcome back, Boss.`
- The dashboard opens immediately without asking for a password.

### Test Case 6: Generate a Recipe With Manual Activity Input

Steps:

1. Log in.
2. Choose `Generate Personalized AI Recipe`.
3. Select a fitness goal.
4. Enter fridge ingredients.
5. Answer `n` when asked about Apple Health import.
6. Enter a manual activity description.
7. Provide a valid DeepSeek API key if prompted.

Sample dialogue:

```text
Select an option (1-2): _1_
Select an option (1-3): _2_
What ingredients are in your fridge right now? (eg. 1kg pork, 4 eggs): _chicken breast, broccoli, rice_
Import your export.zip now? (y/n): _n_
Please manually enter today's workout (e.g., 'ran 10km', 'sedentary'): _ran 5km and walked 8000 steps_
⚠️ DEEPSEEK_API_KEY not found. Please paste your DeepSeek API Key here: _your_api_key_here_
```

Expected result:

- The program shows `YOUR PERSONALIZED AI RECIPE`.
- The response should reflect the chosen goal, ingredients, and manual activity input.
- If the API key is invalid or there is no internet connection, the program prints a DeepSeek connection error instead.

### Test Case 7: Import Apple Health Data Successfully

Steps:

1. Log in and open `Generate Personalized AI Recipe`.
2. Select any goal and enter ingredients.
3. Answer `y` to Apple Health import.
4. In the popup file picker, choose a valid Apple Health `export.zip`.
5. Wait for CSV generation and health-data analysis to finish.
6. Provide a valid API key if prompted.

Sample dialogue:

```text
Select an option (1-2): _1_
Select an option (1-3): _1_
What ingredients are in your fridge right now? (eg. 1kg pork, 4 eggs): _eggs, spinach, oats_
Import your export.zip now? (y/n): _y_
```

Expected result:

- A new folder named after the selected zip file is created beside `project.py`.
- CSV files such as `Record.csv` are generated.
- The terminal prints a summary like `Recorded Date: ..., Total Steps: ..., Active Energy Burned: ... kcal`.
- The AI recipe uses the imported health summary instead of manual activity text.

### Test Case 8: Cancel Apple Health Import and Fall Back to Manual Input

Steps:

1. Start recipe generation.
2. Answer `y` to Apple Health import.
3. Cancel the popup file picker instead of choosing a file.
4. Enter manual activity when prompted.

Sample dialogue:

```text
Import your export.zip now? (y/n): _y_
[Cancel the file picker window]
Please manually enter today's workout (e.g., 'ran 10km', 'sedentary'): _sedentary_
```

Expected result:

- The program prints `No file selected. Reverting to manual input.`
- The meal-generation flow continues normally with manual activity data.

## Tech Stack

- `tkinter` for file selection
- `pandas` for CSV analysis
- `lxml` for XML parsing
- `tqdm` for conversion progress display
- `openai` Python SDK targeting the DeepSeek API endpoint

## Authors

- Wang Zejia
- You Xuanhe
