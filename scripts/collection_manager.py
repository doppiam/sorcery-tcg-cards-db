import csv
import json
import os
import subprocess
import platform
from collections import defaultdict


class CollectionManager:
    def __init__(self, collection_dir="collections", json_dir="data/collections"):
        self.collection_dir = collection_dir
        self.json_dir = json_dir
        self.OUTPUT_DIR = "collections"
        os.makedirs(self.collection_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)

    def delete_collection(self, collection_name):
        csv_path = os.path.join(self.collection_dir, f"{collection_name}.csv")
        json_path = os.path.join(self.json_dir, f"{collection_name}.json")

        deleted_any = False

        if os.path.exists(csv_path):
            os.remove(csv_path)
            print(f"Deleted CSV: {csv_path}")
            deleted_any = True

        if os.path.exists(json_path):
            os.remove(json_path)
            print(f"Deleted JSON: {json_path}")
            deleted_any = True

        if not deleted_any:
            print(f"No files found for collection: {collection_name}")
    
    def list_collections(self):
        collections = [f[:-4] for f in os.listdir(self.collection_dir) if f.endswith(".csv")]
        if not collections:
            print("No collections found.")
        else:
            print("Available Collections:")
            for name in sorted(collections):
                print(f" - {name}")

    def create_collection(self, card_data, coll_name):
        # Create one CSV file per set from the given card JSON data.
        sets_data = []

        for card in card_data:
            name = card.get("name", "")
            element = card.get("elements", "")
            subtype = card.get("subTypes", "")
            base_type = card.get("guardian", {}).get("type", "")
            base_rarity = card.get("guardian", {}).get("rarity", "")
            cost = card.get("guardian", {}).get("cost", "")
            attack = card.get("guardian", {}).get("attack", "")
            defence = card.get("guardian", {}).get("defence", "")

            for set_info in card.get("sets", []):
                set_name = set_info.get("name", "Unknown")
                metadata = set_info.get("metadata", {})

                rarity = metadata.get("rarity", base_rarity)
                type_ = metadata.get("type", base_type)
                cost = metadata.get("cost", cost)
                attack = metadata.get("attack", attack)
                defence = metadata.get("defence", defence)

                for variant in set_info.get("variants", []):
                    sets_data.append({
                        "name": name,
                        "set": set_name.lower().replace(" ", "_"),
                        "type": type_,
                        "subtype": subtype,
                        "element": element,
                        "rarity": rarity,
                        "cost": cost,
                        "attack": attack,
                        "defence": defence,
                        "finish": variant.get("finish", ""),
                        "product": variant.get("product", ""),
                        "artist": variant.get("artist", ""),
                        "variant": variant.get("slug", ""),
                        "owned_quantity": 0
                    })

        headers = ["name", "set", "type", "subtype", "element", "rarity", "cost", "attack", "defence",
                   "finish", "product", "artist", "variant", "owned_quantity"]

        file_path = os.path.join(self.OUTPUT_DIR, f"{coll_name}.csv")

        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(sets_data)

        print(f"CSVs written to `{self.OUTPUT_DIR}`.")

        self.csv_to_json(coll_name)

    def csv_to_json(self, collection_name):
        csv_path = os.path.join(self.collection_dir, f"{collection_name}.csv")
        json_path = os.path.join(self.json_dir, f"{collection_name}.json")

        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return None

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = list(reader)

        with open(json_path, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return json_path

    def generate_stats(self, collection_name):
        self.csv_to_json(collection_name)
        json_path = os.path.join(self.json_dir, f"{collection_name}.json")
        if not os.path.exists(json_path):
            print(f"JSON file not found: {json_path}")
            return

        with open(json_path, mode="r", encoding="utf-8") as f:
            rows = json.load(f)

        grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for row in rows:
            set_ = row["set"]
            rarity = row["rarity"]
            finish = row["finish"]
            grouped[set_][rarity][finish].append(row)

        print(f"\nStats for Collection: {collection_name}")
        print(f"{'-'*50}\n")

        grand_total_unique = 0
        grand_total_all = 0
        grand_total_physical = 0

        for set_name in sorted(grouped):
            print(f"Set: {set_name}")
            set_total_unique = 0
            set_total_all = 0
            set_total_physical = 0

            for rarity in sorted(grouped[set_name]):
                print(f"  Rarity: {rarity}")
                for finish in sorted(grouped[set_name][rarity]):
                    cards = grouped[set_name][rarity][finish]
                    unique_owned = sum(1 for card in cards if int(card["owned_quantity"]) > 0)
                    total_available = len(cards)
                    copies_owned = sum(int(card["owned_quantity"]) for card in cards)

                    set_total_unique += unique_owned
                    set_total_all += total_available
                    set_total_physical += copies_owned

                    print(f"    {finish:<9}: {unique_owned} owned / {total_available} total ({total_available - unique_owned} missing)")

            print(f"  Set Summary: {set_total_unique} unique owned / {set_total_all} total")
            print(f"  Collection: {set_total_physical} total physical cards\n")

            grand_total_unique += set_total_unique
            grand_total_all += set_total_all
            grand_total_physical += set_total_physical

        print(f"{'='*50}")
        print(f"Collection Summary: {grand_total_unique} unique cards owned / {grand_total_all} total")
        print(f"Physical Cards Owned: {grand_total_physical}")
        print(f"Missing Unique Cards: {grand_total_all - grand_total_unique}\n")
    
    def open_collection(self, collection_name):
        filepath = os.path.join(self.collection_dir, f"{collection_name}.csv")
        if not os.path.exists(filepath):
            print(f"Collection file not found: {filepath}")
            return

        print(f"Opening collection: {filepath}")
        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", filepath])
            else:  # Linux and others
                subprocess.run(["xdg-open", filepath])
        except Exception as e:
            print(f"Failed to open file: {e}")
    
    def sync_json(self, collection_name):
        """Sync the JSON version of the collection with the current CSV."""
        json_file = self.csv_to_json(collection_name)
        print(f"{collection_name} synced successfully.")
