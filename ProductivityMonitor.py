import time
from datetime import datetime
import random
from PIL import Image, ImageFilter
import pyscreenshot
import pathlib
import json
import threading
from CTkMessagebox import CTkMessagebox


class ProductivityMonitor:
    def __init__(self, save_dir, bin_day, interval_min, interval_max, classify_screenshot, parent_window=None, pixel_size=20):
        self.save_dir = save_dir
        self.bin_day = bin_day
        self.interval_min = interval_min
        self.interval_max = interval_max
        self.pixel_size = pixel_size
        self.font_scale = 1.5 
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.classify_screenshot = classify_screenshot
        self.parent_window = parent_window

    def take_screenshot(self):
        try:
            screen = pyscreenshot.grab(backend='gnome-screenshot')
            return screen
        except Exception as e:
            print(f"Screenshot error: {e}")
            raise

    def pixelate_image(self, image):
        small = image.resize(
            (image.size[0] // self.pixel_size, image.size[1] // self.pixel_size),
            Image.NEAREST
        )
        result = small.resize(image.size, Image.NEAREST)
        return result.filter(ImageFilter.GaussianBlur(radius=1))

    def save_screenshot(self, image):
        save_path = pathlib.Path(self.save_dir) / self.bin_day
        save_path.mkdir(parents=True, exist_ok=True)

        time = datetime.now()
        time_label = time.strftime('%-I:%M %p (%Y/%m/%d)')
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'screenshot_{timestamp}.png'
        image_path = save_path / filename
        image.save(image_path)
        print(f"Saved: {image_path}")

        # Update JSON file
        json_file = save_path / "screenshots.json"
        if not json_file.exists():
            self.initialize_json()
            
        screenshot_entry = {
            "filename": filename,
            "classification": "none",
        }
        try:
            with open(json_file, 'r+') as f:
                data = json.load(f)
                data["screenshots"].append(screenshot_entry)
                f.seek(0)
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error updating JSON file: {e}")
        
        # Display GUI for classification
        if self.parent_window:
            self.parent_window.after(0, lambda: self.classify_screenshot(image_path, json_file, screenshot_entry, time_label, True))
        else:
            print("Error: No parent window provided for classification.")

    def run_loop(self):
        screenshots_taken = 0
        start_time = time.time()

        while self.running:
            image = self.take_screenshot()
            pixelated = self.pixelate_image(image)
            self.save_screenshot(pixelated)
            screenshots_taken += 1

            elapsed_time = time.time() - start_time
            rate = screenshots_taken / (elapsed_time / 3600)
            print(f"Screenshots taken: {screenshots_taken} (Rate: {rate:.1f}/hour)")

            wait_time = random.randint(self.interval_min, self.interval_max)
            if self.stop_event.wait(timeout=wait_time):
                break

    def get_save_path(self):
        return pathlib.Path(self.save_dir) / self.bin_day

    def get_json_path(self):
        save_path = self.get_save_path()
        json_file = save_path / "screenshots.json"
        if not json_file.exists():
            self.initialize_json()
        return json_file

    def initialize_json(self):
        save_path = self.get_save_path()
        save_path.mkdir(parents=True, exist_ok=True)
        json_file = save_path / "screenshots.json"

        if not json_file.exists():
            initial_data = {
                "day": self.bin_day,
                "screenshots": []
            }
            with open(json_file, 'w') as f:
                json.dump(initial_data, f)

    def update_day(self, new_day: str):
        # Switch folders if user updates day
        self.bin_day = new_day
        self.initialize_json() 

    def start(self):
        if not self.running:
            self.running = True
            self.stop_event.clear()
            self.initialize_json() 
            self.thread = threading.Thread(target=self.run_loop)
            self.thread.start()

    def stop(self):
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join()
