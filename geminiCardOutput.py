import json
import os
import requests
import textwrap

# --- Configuration ---
# IMPORTANT: Set your Gemini API key as an environment variable named 'GEMINI_API_KEY'
# How to set an environment variable:
# - Linux/macOS: export GEMINI_API_KEY='your_api_key_here'
# - Windows: set GEMINI_API_KEY='your_api_key_here'
# You can get an API key from Google AI Studio.
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# --- Robust File Path ---
# Get the absolute path of the directory where the script is located.
# This makes the script runnable from any location.
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ is not defined in some interactive environments (like certain notebooks)
    SCRIPT_DIR = os.getcwd() 
# Join the script directory path with the data folder and filename.
JSON_FILE_PATH = os.path.join(SCRIPT_DIR, 'data', 'credit-cards.json')


def load_credit_cards(filepath):
    """
    Loads credit card data from a JSON file using a robust path.

    Args:
        filepath (str): The path to the JSON file.

    Returns:
        list: A list of dictionaries, where each dictionary is a credit card.
              Returns None if the file is not found or is invalid.
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file was not found at the expected path: {filepath}")
        print("Please make sure you have a 'data' folder in the same directory as the script,")
        print("and that 'credit-card.json' is inside that 'data' folder.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{filepath}' is not a valid JSON file.")
        return None

def get_user_query():
    """
    Prompts the user to describe their ideal credit card.

    Returns:
        str: The user's description.
    """
    print("\nPlease describe the type of credit card you are looking for.")
    print("For example: 'I want a card with no annual fee and good travel rewards.'")
    return input("> ")

def find_best_card(card_list, user_query):
    """
    Uses the Gemini API to find the best card based on a user's query.

    Args:
        card_list (list): The list of available credit cards.
        user_query (str): The user's description of their desired card.

    Returns:
        dict: The dictionary of the recommended card, or None if an error occurs.
    """
    if not API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return None

    # We serialize the list of cards into a JSON string to send to the model.
    cards_json_string = json.dumps(card_list, indent=2)

    # This prompt is engineered to get a clean JSON object as a response.
    prompt = textwrap.dedent(f"""
        You are an expert credit card recommendation assistant.
        Your task is to analyze a user's request and find the single best matching credit card from a provided JSON list.

        Here is the list of available credit cards:
        {cards_json_string}

        Here is the user's request:
        "{user_query}"

        Based on the user's request, please identify the single best card from the list.
        Your response MUST be ONLY the JSON object of the recommended card from the list provided.
        Do not add any explanation, introduction, or markdown formatting.
    """)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    headers = {
        'Content-Type': 'application/json'
    }
    
    card_text = "" # Initialize card_text to be available in the final except block
    try:
        print("\nAsking Gemini to find the best card for you...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)

        response_data = response.json()
        
        # Extract the text content from the API response
        card_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        # --- FIX: Clean the response to remove markdown formatting ---
        # The API sometimes returns the JSON wrapped in ```json ... ```
        # This code finds the start and end of the JSON object to extract it.
        if '```' in card_text:
            start = card_text.find('{')
            end = card_text.rfind('}') + 1
            if start != -1 and end != 0:
                 card_text = card_text[start:end]

        # The model should return a clean JSON string, so we parse it.
        recommended_card = json.loads(card_text)
        return recommended_card

    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")
        return None
    except (KeyError, IndexError):
        print("Error: Could not parse the response from the Gemini API.")
        print("Raw response:", response.text)
        return None
    except json.JSONDecodeError:
        print("Error: Failed to decode the JSON response from the API.")
        print("Received text:", card_text)
        return None


def format_card(card):
    """
    Nicely prints the details of a credit card.
    This function is updated to handle multiple JSON formats.

    Args:
        card (dict): The credit card dictionary to display.
    """
    if not card:
        return "Could not find a recommendation."

    lines = []
    lines.append("--- Recommended Card ---")
    # Handle multiple possible keys for the same data
    name = card.get('card_name', card.get('name', 'N/A'))
    issuer = card.get('issuer', 'N/A')
    annual_fee = card.get('annual_fee', card.get('annualFee', 'N/A'))

    lines.append(f"Name:         {name}")
    lines.append(f"Issuer:       {issuer}")
    lines.append(f"Annual Fee:   ${annual_fee}")

    # --- Improved Formatting Logic ---

    # Attempt to parse rewards from the original format
    rewards_type = card.get('rewards_type')
    if rewards_type:
        lines.append(f"Rewards Type: {', '.join(rewards_type)}")
    # Otherwise, parse rewards from the new format
    elif 'universalCashbackPercent' in card:
        cashback = card.get('universalCashbackPercent', 0)
        if cashback > 0:
            lines.append(f"Rewards:      {cashback}% universal cash back.")
    
    # Attempt to parse welcome bonus from the original format
    welcome_bonus = card.get('welcome_bonus')
    if welcome_bonus:
         lines.append(f"Welcome Bonus: {welcome_bonus}")
    # Otherwise, parse the 'offers' array from the new format
    elif 'offers' in card and card['offers']:
        offer = card['offers'][0] # Get the first offer
        spend = offer.get('spend')
        days = offer.get('days')
        amount = offer.get('amount', [{}])[0].get('amount', 0)
        if amount and spend and days:
            lines.append(f"Welcome Bonus: Earn ${amount} after spending ${spend} in the first {days} days.")

    # Attempt to get features from the original format
    features = card.get('features', [])
    # Also add features from the new format
    if 'credits' in card and card['credits']:
        for credit in card['credits']:
            desc = credit.get('description', 'N/A')
            val = credit.get('value', 0)
            features.append(f"${val} {desc} credit")
    
    if card.get('url'):
        features.append(f"More info: {card.get('url')}")

    if features:
        lines.append("Features:")
        for feature in features:
            lines.append(f"  - {feature}")
    
    lines.append("------------------------")
    return "\n".join(lines)


def get_recommended_card(user_query):
    """
    Main function to run the credit card parser program.
    """
    cards = load_credit_cards(JSON_FILE_PATH)
    if not cards:
        return "Could not load credit card data."
    card = find_best_card(cards, user_query)
    return format_card(card)

# Only run main if executed directly
if __name__ == "__main__":
    print("--- Credit Card Finder powered by Gemini ---")
    cards = load_credit_cards(JSON_FILE_PATH)
    if not cards:
        exit()
    user_query = input("> ")
    card = find_best_card(cards, user_query)
    print(format_card(card))
