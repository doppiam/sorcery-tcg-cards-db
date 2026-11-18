# Sorcery TCG Cards Database - Scripts

This folder contains automation scripts for maintaining the card image database.

## 📝 Scripts

### `import_set.py`

Imports one set from the [official API](https://api.sorcerytcg.com/) and its
downloaded PNGs from the [official image folder](https://drive.google.com/drive/folders/17IrJkRGmIU9fDSTU2JQEU9JlFzb5liLJ).
The current API uses `engine` and `printings`; the importer translates them to
the existing `guardian`, `sets`, and `variants` schema. It retains existing card
names, earlier set appearances, and legacy slugs, and refreshes gameplay fields
for cards in the imported set. Other cards are left unchanged.

Download the set's original PNGs into a local directory, keeping their official
numeric filenames (for example, `008-frost_mage-pd-s.png`), then run:

```bash
python3 scripts/import_set.py \
  --set "Frost Mage Vs. Lavamancer" \
  --prefix fro \
  --images-dir /path/to/downloaded/images
python3 scripts/generate_thumbnails.py
```

The importer requires only Python's standard library. Thumbnail generation also
requires Pillow. Use `--api-json /path/to/cards.json` to reuse a previously saved
official API response. Repeating an import updates matching variants without
duplicating them. It imports only the specified set; it does not migrate the
rest of the database to the new API format.

### `generate_thumbnails.py`

Automatically generates JPG thumbnails from PNG card images.

**What it does:**
- Recursively scans `data/imgs/full/` for all PNG files
- Creates corresponding JPG thumbnails in `data/imgs/thumbs/`
- Preserves the exact folder structure (set/product/filename)
- Only regenerates thumbnails that are outdated or missing
- Works with **any set name and product type** automatically

**Configuration:**
- Thumbnail width: 300px (height scales proportionally)
- JPEG quality: 85%
- Format: PNG → JPG conversion with white background

**Usage:**

```bash
# Run from repository root
python scripts/generate_thumbnails.py
```

**Requirements:**
- Python 3.7+
- Pillow library (`pip install Pillow`)

**Example output:**
```
Found 2500 PNG images
Thumbnail size: 300px width
JPEG quality: 85%

✨ Created thumbnail 50/2500: Gothic/b_f/zombie_bruiser_b_f.jpg
✨ Created thumbnail 100/2500: Promotional/ai_f/skeleton_ai_f.jpg
...

Summary:
  ✅ Processed: 450
     - Created: 450
     - Updated: 0
  ⏭️  Skipped (up-to-date): 2050
  ❌ Errors: 0
  📊 Total images: 2500
```

---

## 🤖 GitHub Actions

The thumbnail generation runs automatically via GitHub Actions when:
- PNG images are pushed to `data/imgs/full/**`
- Manual trigger via "Actions" tab → "Generate Card Thumbnails" → "Run workflow"

See `.github/workflows/generate-thumbnails.yml` for details.

---

## 🆕 Adding New Sets or Product Types

The script is **fully automatic** and doesn't require configuration when adding:
- New sets (e.g., Gothic, Promotional)
- New product types (e.g., ai, tc, op, du)
- New card images

Just add the PNG files to the correct folder structure:
```
data/imgs/full/<SetName>/<product>_<finish>/<cardname>_<product>_<finish>.png
```

The script will automatically:
1. Detect the new images
2. Create the matching folder structure in `thumbs/`
3. Generate the thumbnails

---

## 🔧 Manual Testing

To test thumbnail generation locally:

```bash
# Install dependencies
pip install Pillow

# Run the script
python scripts/generate_thumbnails.py

# Check the output in data/imgs/thumbs/
```

