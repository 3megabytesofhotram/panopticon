import os
import json
import customtkinter as ctk
import pandas as pd
import datetime
from MinimalMessageBox import MinimalMessageBox
from tkinter import filedialog

from SingleInstance import SingleInstance, SingleInstanceException
from JsonVisualizerFrame import JsonVisualizerFrame
from ProductivityMonitor import ProductivityMonitor

class PanopticonGUI(ctk.CTk):
    def __init__(self):
        super().__init__(wm_class="Panopticon")

        # Set window title and size
        self.title("Panopticon")
        self.geometry("1200x800")  # Increased size by 50%
        self.minsize(800, 800)

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Load config
        self.config_file = os.path.expanduser("~/.config/panopticon/settings.json")
        self.load_config()

        # Set data bin to day program was started
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")

        # Initialize monitor
        self.monitor = ProductivityMonitor(
            save_dir=self.config["save_dir"],
            bin_day=self.today,
            interval_min=self.config["interval_min"],
            interval_max=self.config["interval_max"],
            classify_screenshot=self.classify_screenshot,
            parent_window=self,
            pixel_size=self.config["pixel_size"],
        )

        self.font_scale = 1.5  # Scaling factor for fonts
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        default_config = {
            "save_dir": os.path.join(os.path.dirname(os.path.abspath(__file__)),"screenshots"),
            "interval_min": 30,
            "interval_max": 600,
            "pixel_size": 7
        }

        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = default_config
            self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def create_widgets(self):
        container = ctk.CTkFrame(self, fg_color="#242424")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Create left frame for control and settings widgets
        self.left_frame = ctk.CTkFrame(container, width= 3 * self.winfo_width() // 7, fg_color="#242424")
        self.left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10), pady=0)

        # Create right frame for JsonVisualizerFrame
        self.right_frame = ctk.CTkFrame(container, width=4 * self.winfo_width() // 7, fg_color="#2B2B2B")
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)

        # Initially, JsonVisualizerFrame is not created
        self.visualizer_frame = None

        self.create_control_widgets(self.left_frame)
        self.create_settings_widgets(self.left_frame)

    def create_control_widgets(self, parent):
        control_frame = ctk.CTkFrame(parent)
        control_frame.pack(fill="x", pady=(0, 20))

        control_label = ctk.CTkLabel(control_frame, text="Controls", font=("", int(20 * self.font_scale), "bold"))
        control_label.pack(pady=(16,10))

        self.toggle_button = ctk.CTkButton(
            control_frame, text="Start", font=("", int(16 * self.font_scale)), command=self.toggle_monitoring, fg_color="#4CAF50", hover_color="#66BB6A"
        )
        self.toggle_button.pack(fill="x", padx=20, pady=5)

        display_button = ctk.CTkButton(
            control_frame, 
            text="Load Data", 
            font=("", int(16 * self.font_scale)), 
            command=self.reload_visualizer_frame
        )
        display_button.pack(fill="x", padx=20, pady=(5,16))

    def create_settings_widgets(self, parent):
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="both", expand=True)

        settings_label = ctk.CTkLabel(settings_frame, text="Settings", font=("", int(20 * self.font_scale), "bold"))
        settings_label.pack(pady=(20,16))

        ctk.CTkLabel(settings_frame,
                     text="Recording Day (YYYY-MM-DD):",
                     font=("", int(14 * self.font_scale))
        ).pack(anchor="w", padx=20)

        self.day_entry = ctk.CTkEntry(settings_frame,
                                      font=("", int(14 * self.font_scale)))
        self.day_entry.pack(fill="x", padx=20, pady=(0, 10))
        self.day_entry.insert(0, self.today)              # pre-fill today

        ctk.CTkButton(settings_frame,
                      text="Set Day",
                      font=("", int(14 * self.font_scale)),
                      command=self.update_day
        ).pack(fill="x", padx=20, pady=(0, 18))

        ctk.CTkLabel(settings_frame, text="Min Interval (seconds):", font=("", int(14 * self.font_scale))).pack(anchor="w", padx=20)
        self.min_interval = ctk.CTkEntry(settings_frame, font=("", int(14 * self.font_scale)))
        self.min_interval.pack(fill="x", padx=20, pady=(0, 10))
        self.min_interval.insert(0, str(self.config["interval_min"]))

        ctk.CTkLabel(settings_frame, text="Max Interval (seconds):", font=("", int(14 * self.font_scale))).pack(anchor="w", padx=20)
        self.max_interval = ctk.CTkEntry(settings_frame, font=("", int(14 * self.font_scale)))
        self.max_interval.pack(fill="x", padx=20, pady=(0, 10))
        self.max_interval.insert(0, str(self.config["interval_max"]))

        ctk.CTkLabel(settings_frame, text="Pixel Size:", font=("", int(14 * self.font_scale))).pack(anchor="w", padx=20)
        self.pixel_size = ctk.CTkEntry(settings_frame, font=("", int(14 * self.font_scale)))
        self.pixel_size.pack(fill="x", padx=20, pady=(0, 10))
        self.pixel_size.insert(0, str(self.config["pixel_size"]))

        self.save_dir_var = ctk.StringVar(value=self.config["save_dir"])
        ctk.CTkLabel(settings_frame, text="Save directory:",
                    font=("", int(14 * self.font_scale))
        ).pack(anchor="w", padx=20)

        ctk.CTkEntry(settings_frame,
                    textvariable=self.save_dir_var,
                    state="readonly",
                    font=("", int(14 * self.font_scale))
        ).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(settings_frame,
                      text="Choose Folder",
                      font=("", int(14 * self.font_scale)),
                      command=self.choose_save_dir
        ).pack(fill="x", padx=20, pady=(0, 18))

        button_frame = ctk.CTkFrame(settings_frame)
        button_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(button_frame, text="Save Settings", font=("", int(14 * self.font_scale)), command=self.save_settings).pack(side="left", padx=(0, 5), expand=True)
        ctk.CTkButton(button_frame, text="Reset to Default", font=("", int(14 * self.font_scale)), command=self.reset_settings).pack(side="left", padx=(5, 0), expand=True)
    
    def reload_visualizer_frame(self):
      print("\nReloading visualizer frame...")
      if self.visualizer_frame:
          self.visualizer_frame.refresh()
      else:
        # Load the JSON file path and recreate the JsonVisualizerFrame
        print("No visualizer frame found, recreating...")
        json_path = self.monitor.get_json_path()  # Adjust path logic if needed
        save_path = self.monitor.get_save_path()
        vf_margin = 10
        self.visualizer_frame = JsonVisualizerFrame(self.right_frame, self.classify_screenshot, json_path=json_path, save_path=save_path, margin=vf_margin, font_scale=self.font_scale)
        self.visualizer_frame.pack(fill="both", expand=True, padx=vf_margin, pady=vf_margin)

    def toggle_monitoring(self):
        if self.monitor.running:
            self.monitor.stop()
            self.toggle_button.configure(text="Start", fg_color="#4CAF50", hover_color="#66BB6A")
        else:
            self.monitor.start()
            self.toggle_button.configure(text="Stop", fg_color="#7B61FF", hover_color="#9780FF")

    def classify_screenshot(self, image_path, json_file, screenshot_entry, time_label, new):
        print("Classifying screenshot...")
        # Create a messagebox to classify the screenshot
        options = [{"label": "On-Task", "color": "#66BB6A", "hover_color": "#66BB6A",
                    "width_ratio": 2},
                    {"label": "Off-Task", "color": "#FF4747", "hover_color": "#FF6B6B", "width_ratio": 2},
                    {"label": "None", "color": "gray", "hover_color": "dimgray", "width_ratio": 1.5},
                    {"label": "X", "color": "#7B61FF", "hover_color": "#F5F5F5", "width_ratio": 0.5}]
        resp = MinimalMessageBox(
                title="Classify Screenshot",
                options=options,
                font_scale=self.font_scale,
                message=f"Screenshot taken at {time_label}:",
                img_path=image_path,
               ).get()
        response = resp

        if response == "X":
            # Remove the screenshot file and JSON entry
            try:
                image_path.unlink()  # Delete the image file
                with open(json_file, 'r+') as f:
                    data = json.load(f)
                    data["screenshots"] = [
                        entry for entry in data["screenshots"]
                        if entry["filename"] != screenshot_entry["filename"]
                    ]
                    f.seek(0)
                    f.truncate()
                    json.dump(data, f, indent=4)
                print(f"Screenshot discarded: {image_path}")
            except Exception as e:
                print(f"Error discarding screenshot: {e}")
        elif response in ["On-Task", "Off-Task", "None"]:
            # Update the JSON entry with the selected classification
            try:
                with open(json_file, 'r+') as f:
                    data = json.load(f)
                    for entry in data["screenshots"]:
                        if entry["filename"] == screenshot_entry["filename"]:
                            entry["classification"] = response.lower()
                            break
                    f.seek(0)
                    f.truncate()
                    json.dump(data, f, indent=4)
                print(f"Screenshot classified as {response.lower()}: {image_path}")
            except Exception as e:
                print(f"Error updating classification: {e}")
        else:
            print(f"No action taken for screenshot: {image_path}")
            return None # response is None
        
        screenshot_entry["classification"] = response.lower()

        if new and not (response == "X"):
          # Reload the visualizer frame entirely if # of ss's changed
          if self.visualizer_frame:
              self.visualizer_frame.add_screenshot_button(image_path, screenshot_entry)
          else:
              self.reload_visualizer_frame()
        
        return response
    
    def update_day(self):
        new_day = self.day_entry.get().strip()
        try:
            datetime.datetime.strptime(new_day, "%Y-%m-%d")
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.")
            return

        self.today = new_day              # update GUI’s own record
        self.monitor.update_day(new_day)  # update ProductivityMonitor

        # Update and refresh JsonVisualizer
        if self.visualizer_frame:
            json_path = self.monitor.get_json_path()
            save_path = self.monitor.get_save_path()
            self.visualizer_frame.update_json_path(json_path, save_path)
        else:
            self.reload_visualizer_frame()

        print(f"Recording day set to {new_day}")

    def choose_save_dir(self):
        new_dir = filedialog.askdirectory(
            title="Select screenshot folder",
            initialdir=self.config["save_dir"]
        )
        if not new_dir: 
            return

        # change save directory
        self.config["save_dir"] = new_dir
        self.monitor.save_dir = new_dir
        self.visualizer_frame.save_path = new_dir
        self.save_dir_var.set(new_dir)
        self.save_config() # save automatically

    def reset_settings(self):
        self.min_interval.delete(0, 'end')
        self.max_interval.delete(0, 'end')
        self.pixel_size.delete(0, 'end')
        self.min_interval.insert(0, "30")
        self.max_interval.insert(0, "600")
        self.pixel_size.insert(0, "7")

    def save_settings(self):
        try:
            self.config["interval_min"] = int(self.min_interval.get())
            self.config["interval_max"] = int(self.max_interval.get())
            self.config["pixel_size"] = int(self.pixel_size.get())
            self.save_config()
            print("Settings saved successfully")
        except ValueError:
            print("Error: Please enter valid numbers for all settings")

    def on_closing(self):
        print("Closing...")
        if self.monitor.running:
            self.monitor.stop()
        self.quit()

def main():
    try:
        with SingleInstance():
            app = PanopticonGUI()
            app.mainloop()
    except SingleInstanceException:
        print("Another instance is already running")
        exit(1)

if __name__ == "__main__":
    main()
