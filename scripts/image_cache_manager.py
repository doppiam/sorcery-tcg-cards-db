import os
import requests
from PIL import Image


class ImageCacheManager:
    def __init__(self, cache_dir="data/imgs"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.base_url = "https://raw.githubusercontent.com/fortinj/sorcery-tcg-cards-db/main"

    def update_images_cache(self, data, mode="update"):
        assert mode in ("force", "update"), "Mode must be 'force' or 'update'"

        downloaded = 0
        thumb_created = 0
        full_skipped = 0
        thumb_skipped = 0
        missing = []

        for card in data:
            for set_info in card.get("sets", []):
                set_name = set_info.get("name", "Unknown").replace(" ","_")
                for variant in set_info.get("variants", []):
                    slug = variant.get("slug")
                    if not slug:
                        continue

                    try:
                        variant_code = "_".join(slug.split("_")[-2:])
                        image_name = "_".join(slug.split("_")[1:]) + ".png"
                    except IndexError:
                        print(f"Failed to parse slug: {slug}")
                        continue
                    
                    remote_path = f"{self.base_url}/{set_name}/{variant_code}/{image_name}"
                    full_img_local_path = os.path.join(self.cache_dir, set_name, variant_code, image_name)
                    thumb_img_local_path = os.path.join(self.cache_dir, set_name, variant_code, f"t_{image_name}")

                    if os.path.exists(full_img_local_path) and mode == "update":
                        full_skipped += 1
                        if (self.generate_thumbnails(full_img_local_path, thumb_img_local_path)):
                            thumb_created += 1
                        else:
                            thumb_skipped += 1

                        continue
                    
                    os.makedirs(os.path.dirname(full_img_local_path), exist_ok=True)

                    try:
                        response = requests.get(remote_path, timeout=10)
                        response.raise_for_status()
                        with open(full_img_local_path, "wb") as f:
                            f.write(response.content)
                        downloaded += 1

                    except Exception as e:
                        print(f"Failed to download {image_name}: {e}")
                        missing.append(slug)
                    
                    if (self.generate_thumbnails(full_img_local_path, thumb_img_local_path)):
                        thumb_created += 1
                    else:
                        print(f"Failed to produce thumbnail for {image_name}.")
                        

        print(f"\nImage cache updated: {downloaded} downloaded, {full_skipped} skipped (mode: {mode})")
        print(f"\nThumbnail cache updated: {thumb_created} created, {thumb_skipped} skipped (mode: {mode})")
        if missing:
            print(f"{len(missing)} images failed to download. See log above.")
    
    def generate_thumbnails(self, full_image_path, thumbnail_path, max_size=(96, 96)):
        if os.path.exists(thumbnail_path):
            return False
        try:
            with Image.open(full_image_path) as img:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, format="PNG")
            print(f"Generated thumbnail: {thumbnail_path}")
            return True
        except Exception as e:
            print(f"Failed to process {full_image_path}: {e}")
