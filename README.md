# FridgeFit

FridgeFit is an intelligent healthy eating assistant application that generates personalized nutrition recipes by analyzing users' Apple Health data and available ingredients in their fridge using AI.

## Features

- **User Authentication System**: Secure registration and login functionality
- **Apple Health Data Import**: Automatically parse Apple Health exported XML data
- **Health Data Analysis**: Extract step count and active energy burned data
- **AI-Powered Recipe Generation**: Generate personalized dietary recommendations using DeepSeek API
- **Fitness Goal Customization**: Support for three goals - Weight Loss, Muscle Gain, and Maintenance

## Requirements

### Environment

- Python 3.8+

### Installation

1. Clone or download this project
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up DeepSeek API Key (choose one method):
   - Method 1: Set environment variable `DEEPSEEK_API_KEY`
   - Method 2: Enter directly when running the program

## Usage

1. Run the program:

```bash
python TEST.py
```

2. Register an account for first-time use (default admin account: admin / 123)

3. After login, select "Generate Personalized AI Recipe"

4. Choose your fitness goal and enter ingredients available in your fridge

5. Optionally import Apple Health data or manually enter your activity level

6. Receive your AI-generated personalized recipe

## Apple Health Data Export Guide

1. Open the "Health" app on your iPhone
2. Tap your profile picture in the top right corner
3. Select "Export All Health Data"
4. Save the generated export.zip file to your computer
5. Select this file in FridgeFit for import

## Project Structure

```
.
├── TEST.py              # Main program entry
├── requirements.txt     # Python dependencies
├── users.json          # User data storage
└── README.md           # Project documentation
```

## Tech Stack

- **GUI**: tkinter (file selection dialog)
- **Data Processing**: pandas, lxml
- **Progress Display**: tqdm
- **AI API**: OpenAI SDK + DeepSeek API

## Core Modules

| Module | Function | Developer |
|--------|----------|-----------|
| Menu & Login System | User registration, login, main menu | Wang Zejia |
| XML to CSV | Parse Apple Health exported data | You Xuanhe |
| Health Data Reader | Analyze step count and energy burned | Wang Zejia |
| DeepSeek API | AI recipe generation API calls | You Xuanhe |
| Prompt Engineering | AI prompt design and optimization | Wang Zejia |
| Program Execution Flow | Main program loop and state management | Wang Zejia |

## Notes

- Password must be at least 8 characters long
- Apple Health export files may be large and take time to parse
- Valid DeepSeek API key is required for AI recipe features
- All user data is stored locally in `users.json`

## License

This project is for educational and demonstration purposes only.

## Authors

- Wang Zejia
- You Xuanhe
