import os
import json
import requests


class CardDatabase:
    API_URL = "https://api.sorcerytcg.com/api/cards"
    JSON_PATH = "data/cards/cards.json"

    def __init__(self):
        os.makedirs(os.path.dirname(self.JSON_PATH), exist_ok=True)

    def get_cards(self):
        print("Fetching cards from API...")
        response = requests.get(self.API_URL)
        response.raise_for_status()
        return response.json()

    def save_to_json(self, data):
        with open(self.JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Card database saved to {self.JSON_PATH}")

    def load_from_json(self):
        with open(self.JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
