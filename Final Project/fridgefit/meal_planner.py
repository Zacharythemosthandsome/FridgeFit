"""Interactive meal-planning flow and DeepSeek integration."""

import os
import time

from .config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, DEEPSEEK_SYSTEM_PROMPT
from .health import get_health_data_summary, process_apple_health_zip

MANUAL_ACTIVITY_PROMPT = "Please manually enter today's workout (e.g., 'ran 10km', 'sedentary'): "

# ------------------------------------- AI meal plan manu system (Wang Zejia) ------------------------------

def generate_ai_meal_plan(username: str) -> None:
    """Run the interactive AI meal plan flow for the logged-in user."""
    _ = username
    print("\n==============================")
    print("     AI MEAL PLAN GENERATOR")
    print("==============================")

    goal = _prompt_for_goal()
    ingredients = input(
        "\nWhat ingredients are in your fridge right now? (eg. 1kg pork, 4 eggs): "
    ).strip()
    activity_level = _prompt_for_activity_level()

    print("\n[AI] Synthesizing data via DeepSeek API... Please wait.")
    api_key = _get_api_key()
    if not api_key:
        print("\n[Error] API Key is required. Returning to Dashboard...")
        time.sleep(2)
        return

    prompt = _build_recipe_prompt(goal, ingredients, activity_level)

# ------------------------------------- Get Respond From AI (You Xuanhe)------------------------------
    try:
        response_text = _request_recipe(prompt, api_key)
        print("\n" + "=" * 50)
        print("🍽️ YOUR PERSONALIZED AI RECIPE 🍽️")
        print("=" * 50)
        print(response_text)
        print("=" * 50)
    except Exception as error:
        print(f"\n[Error] DeepSeek API connection failed: {error}")
        print("Hint: Please ensure your API Key is correct and you have internet access.")

    input("\n(Press Enter to return to Dashboard)")

# ------------------------------------- AI meal plan manu system (Wang Zejia) ------------------------------

def _prompt_for_goal() -> str:
    print("Please select your primary fitness goal:")
    print("1. Weight Loss")
    print("2. Muscle Gain")
    print("3. Maintenance")

    while True:
        choice = input("Select an option (1-3): ").strip()
        if choice == "1":
            return "Weight Loss"
        if choice == "2":
            return "Muscle Gain"
        if choice == "3":
            return "Maintenance"
        print("Invalid choice. Please enter 1, 2, or 3.")


def _prompt_for_activity_level() -> str:
    print("\n[Apple Health Integration]")
    print("Would you like to import your Apple Health data for precise dynamic meal adjustment?")
    print("💡 Tip: Go to the 'Health' app on your iPhone > Profile (top right) > 'Export All Health Data'.")
    use_health_data = input("Import your export.zip now? (y/n): ").strip().lower()

    if use_health_data != "y":
        return input(f"\n{MANUAL_ACTIVITY_PROMPT}").strip()

    print("\n[System] Please select your Apple Health export.zip file in the popup window...")
    time.sleep(1)
    output_folder = process_apple_health_zip()

    if output_folder:
        health_summary = get_health_data_summary(output_folder)
        if health_summary:
            print(f"[System] Success! Extracted data: {health_summary}")
            return f"User's precise Apple Health data for the day: {health_summary}"

        print("[System] Data parsing failed. Reverting to manual input.")
        return input(MANUAL_ACTIVITY_PROMPT).strip()

    print("[System] No file selected. Reverting to manual input.")
    return input(MANUAL_ACTIVITY_PROMPT).strip()

# ---------------------------------------- API Key Config (You Xuanhe)----------------------------------------

# Get API KEY from system environment variable
def _get_api_key() -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        api_key = input(
            "\n⚠️ DEEPSEEK_API_KEY not found. Please paste your DeepSeek API Key here: "
        ).strip()
        print("Thinking...")
    return api_key

# ---------------------------- Prompt Building (Wang Zejia)---------------------------------------------

def _build_recipe_prompt(goal: str, ingredients: str, activity_level: str) -> str:
    return f"""
    You are an expert sports nutritionist and master chef for the app FridgeFit.
    User Data:
    - Available Ingredients: {ingredients}
    - Primary Fitness Goal: {goal}
    - Today's Energy Expenditure: {activity_level}

    Please provide a personalized recipe adjusting macros/calories based on their exact energy expenditure today. Include cooking instructions and briefly explain why this fits their goal and activity level. Use markdown.
    """
# ---------------------------- API Calling (You Xuanhe)---------------------------------------------

def _request_recipe(prompt: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": DEEPSEEK_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        stream=False,
    )
    return response.choices[0].message.content
