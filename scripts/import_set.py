#!/usr/bin/env python3
"""Import an official set and its downloaded images into the legacy database."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
from urllib.request import urlopen


API_URL = "https://api.sorcerytcg.com/api/cards"
ROOT = Path(__file__).resolve().parents[1]
ELEMENTS = ("Earth", "Fire", "Water", "Air", "None")
PRODUCTS = {
    "BoxTopper": "Box_Topper",
    "PreconstructedDeck": "Preconstructed_Deck",
    "DraftKit": "Draft_Kit",
    "WelcomeKit": "Welcome_Kit",
    "TeamCovenant": "Team_Covenant",
    "AlphaInvestments": "Alpha_Investments",
    "StarCityGames": "Star_City_Games",
    "OrganizedPlay": "Organized_Play",
}


def metadata(engine):
    """Translate current gameplay fields to the database's existing schema."""
    return {
        "rarity": engine["rarity"],
        "type": engine["type"],
        "rulesText": engine["rules"] or "",
        "cost": engine["cost"],
        "attack": engine["attack"],
        "defence": engine["defense"],
        "life": engine["life"],
        "thresholds": {element: engine[element] for element in ("air", "earth", "fire", "water")},
    }


def import_set(cards, official, set_name, prefix, images_dir):
    """Merge one set, retaining existing card names, slugs, and older editions."""
    result = deepcopy(cards)
    by_name = {card["name"]: card for card in result}
    images = []
    seen = set()
    added = 0
    for source in official:
        printings = [p for p in source["printings"] if p["set"]["name"] == set_name]
        if not printings:
            continue
        engine = source["engine"]
        if engine.get("back") or any(p["meta"].get("back") for p in printings):
            raise ValueError("Double-sided cards need an explicit legacy mapping")
        guardian = metadata(engine)
        card = by_name.get(source["name"])
        if card is None:
            card = {"name": source["name"], "guardian": {}, "elements": "", "subTypes": "", "sets": []}
            result.append(card)
            by_name[card["name"]] = card
            added += 1
        card.update({
            "guardian": guardian,
            "elements": ", ".join(sorted(engine["elements"], key=ELEMENTS.index)),
            "subTypes": ", ".join(engine["subtypes"]),
        })
        edition = next((s for s in card["sets"] if s["name"] == set_name), None)
        if edition is None:
            edition = {
                "name": set_name,
                "releasedAt": printings[0]["set"]["releasedAt"],
                "metadata": deepcopy(guardian),
                "variants": [],
            }
            card["sets"].append(edition)
        edition["releasedAt"] = printings[0]["set"]["releasedAt"]
        edition["metadata"] = deepcopy(guardian)
        for printing in printings:
            if not re.fullmatch(r"[a-z0-9_-]+", printing["slug"]):
                raise ValueError(f"Invalid printing slug: {printing['slug']}")
            code, body = printing["slug"].split("-", 1)
            name, product, finish = body.rsplit("-", 2)
            if code != printing["set"]["code"]:
                raise ValueError("Printing slug does not match its set code")
            slug = f"{prefix}_{name}_{product}_{finish}"
            if slug in seen:
                raise ValueError(f"Duplicate printing: {slug}")
            seen.add(slug)
            source_image = images_dir / (printing["slug"] + ".png")
            if source_image.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError(f"Invalid PNG: {source_image}")
            relative = Path(set_name.replace(" ", "_")) / f"{product}_{finish}" / f"{prefix}-{body}.png"
            images.append((source_image, relative))
            meta = printing["meta"]
            variant = {
                "slug": slug,
                "finish": meta["finish"],
                "product": PRODUCTS.get(meta["product"], meta["product"]),
                "artist": meta["artist"]["name"],
                "flavorText": meta["flavor"] or "",
                "typeText": meta["typeline"],
            }
            previous = next((v for v in edition["variants"] if v["slug"] == slug), None)
            if previous is None:
                edition["variants"].append(variant)
            else:
                previous.update(variant)
    if not images:
        raise ValueError(f"No printings found for set: {set_name}")
    return result, images, added


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", required=True, dest="set_name", help="Exact official set name")
    parser.add_argument("--prefix", required=True, help="Legacy image and variant prefix, e.g. fro")
    parser.add_argument("--images-dir", required=True, type=Path, help="Downloaded official PNGs with numeric prefixes")
    parser.add_argument("--api-json", type=Path, help="Use a saved API response instead of downloading it")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z]{3}", args.prefix):
        parser.error("--prefix must contain three lowercase letters")
    if args.set_name in (".", "..") or "/" in args.set_name or "\\" in args.set_name:
        parser.error("--set must be a single directory name")
    if args.api_json:
        official = json.loads(args.api_json.read_text(encoding="utf-8"))
    else:
        with urlopen(API_URL, timeout=60) as response:
            official = json.load(response)
    database_path = ROOT / "data/db/cards.json"
    cards = json.loads(database_path.read_text(encoding="utf-8"))
    updated, images, added = import_set(cards, official, args.set_name, args.prefix, args.images_dir)
    for source, relative in images:
        target = ROOT / "data/imgs/full" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or source.read_bytes() != target.read_bytes():
            shutil.copy2(source, target)
    serialized = json.dumps(updated, indent=2, ensure_ascii=False) + "\n"
    if database_path.read_text(encoding="utf-8") != serialized:
        temporary = database_path.with_suffix(".json.tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(database_path)
    print(f"Imported {args.set_name}: {len(images)} printings, {added} new cards, {len(updated)} total cards")


if __name__ == "__main__":
    main()
