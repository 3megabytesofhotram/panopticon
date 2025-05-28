import math
import customtkinter as ctk
import json
from datetime import datetime
from functools import partial
import time

class JsonVisualizerFrame(ctk.CTkFrame):
    def __init__(self, parent, classify_screenshot, json_path, save_path, margin=10, font_scale=1, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._parent_size = (parent.winfo_width(), parent.winfo_height())

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._fg_color = "#2B2B2B"  
        self._pad = 12
        self._marg = margin

        self.classify_screenshot = classify_screenshot
        self.json_path = json_path
        self.save_path = save_path
        self.font_scale = font_scale
        self.color_map = {"on-task":  ("#4CAF50", "#66BB6A"),
                          "off-task": ("#FF4747", "#FF6B6B"),
                          "none":     ("dimgray", "gray")}
        self.rev_color_map = {"#4CAF50":"on-task", "#FF4747":"off-task", "dimgray":"none"}

        self.data = self.load_json()
        self.create_widgets()

    def load_json(self):
        try:
            with open(self.json_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return {}

    def get_totals(self):
        screenshots = self.data.get("screenshots", [])
        on_task = sum(1 for s in screenshots if s["classification"] == "on-task")
        off_task = sum(1 for s in screenshots if s["classification"] == "off-task")
        none = len(screenshots) - on_task - off_task

        return on_task, off_task, none

    def create_widgets(self):
        print("\nCreating widgets...")
        self.create_summary_bar()
        self.update_idletasks() # Update summary bar
        self.create_squares_grid()

    def create_summary_bar(self):
      # Prepare container
      print("Creating summary bar...")
      if hasattr(self, "_summary_frame") and self._summary_frame.winfo_exists():
          self._summary_frame.destroy()

      self._summary_frame = ctk.CTkFrame(self, fg_color="#222222")
      self._summary_frame.pack(fill="x", padx=self._pad, pady=self._pad)
      parent_w, _ = self._parent_size
      width = parent_w - (2 * self._pad + 2 * self._marg)
      self._summary_frame.configure(width=width)
      # self._summary_frame.pack_propagate(False)

      lbl_font = ("", int(16 * self.font_scale), "bold")
      self._on_lbl   = ctk.CTkLabel(self._summary_frame, text="", font=lbl_font)
      self._off_lbl  = ctk.CTkLabel(self._summary_frame, text="", font=lbl_font)
      self._none_lbl = ctk.CTkLabel(self._summary_frame, text="", font=lbl_font)

      for lbl in (self._on_lbl, self._off_lbl, self._none_lbl):
          lbl.pack(side="left", padx=14, pady=20)

      # Fill in the figures the first time
      on_task, off_task, none = self.get_totals()
      self.update_totals_display(on_task, off_task, none)

    def update_totals_display(self, on_task, off_task, none):
      self._on_lbl.configure(text=f"On-task: {on_task}")
      self._off_lbl.configure(text=f"Off-task: {off_task}")
      self._none_lbl.configure(text=f"None: {none}")

    def configure_grid_dim(self, total=None):
        # Decide grid dimensions (rows × cols)
        if total is None:
            total = len(self._buttons) 
        mod_total = max(16, total)
        cols = math.ceil(math.sqrt(mod_total))
        rows = math.ceil(mod_total / cols)
        print(f"{total} screenshots found while configuring grid, updated to {mod_total}, creating {rows} rows by {cols} cols")

        return cols, rows

    def create_squares_grid(self) -> None:
        """Lay out screenshot buttons in a responsive square grid."""
        print("Creating square grid...")
        screenshots = self.data.get("screenshots", [])
        if not screenshots:
            return

        # Prepare container
        if hasattr(self, "_grid_frame") and self._grid_frame.winfo_exists():
            self._grid_frame.destroy()
        self._grid_frame = ctk.CTkFrame(self)
        self._grid_frame.pack(fill="both", expand=True, padx=self._pad, pady=self._pad)
        self._grid_frame.pack_propagate(False)

        # Set up grid
        self._grid_dim = self.configure_grid_dim(total=len(screenshots))
        cols, rows = self._grid_dim

        for r in range(rows):
            self._grid_frame.rowconfigure(r, weight=1, uniform="rows")
        for c in range(cols):
            self._grid_frame.columnconfigure(c, weight=1, uniform="cols")

        # Create buttons
        self._buttons = []
        for idx, shot in enumerate(screenshots):
            r, c = divmod(idx, cols)

            # pick colours based on classification
            cls = shot["classification"]
            color, hover = self.color_map.get(cls, ("dimgray", "gray"))

            # Get filename and time label
            fname = shot["filename"]
            img_path = self.save_path / fname

            btn = ctk.CTkButton(
                self._grid_frame,
                text="",
                fg_color=color,
                hover_color=hover,
            )

            # give the callback a handle on the button itself
            btn.configure(
                command=partial(
                    self.update_screenshot,
                    btn,
                    img_path,      
                    shot,
                    fname
                )
            )
            btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
            self._buttons.append(btn)
        
        self._on_frame_resize()  

        print(len(self._buttons))
        print("Finishing square grid...")


    def _on_frame_resize(self):
        # the largest square that fits in every cell
        print("Resizing...")
        old_cols, old_rows = self._grid_frame.grid_size()
        cols, rows = self._grid_dim

        for c in range(cols, old_cols):
            self._grid_frame.columnconfigure(c, weight=0, uniform="", minsize=0)
        for r in range(rows, old_rows):
            self._grid_frame.rowconfigure(r, weight=0, uniform="", minsize=0)

        width = self._grid_frame.winfo_width()
        height = self._grid_frame.winfo_height()

        summary_height = self._summary_frame.winfo_reqheight()
        if width <= 1:
            print("Defaulting via parent size")
            parent_w, parent_h = self._parent_size
            print(f"Parent size is {parent_w} by {parent_h}")
            width = parent_w - (2 * self._pad + 2 * self._marg)
            height = parent_h- (4 * self._pad + + 2 * self._marg + summary_height)
        print(f"Summary height is {summary_height}")

        print(f"Max size is {width} by {height}")
        cell = min(width // cols, height // rows)
        # subtract 6 for 3 x 3 padding size
        size = max(cell - 6, 8)

        print(f"Creating cells of size {size}")
        for r in range(rows):
            self._grid_frame.rowconfigure(r, weight=1, uniform="rows", minsize=size)
        for c in range(cols):
            self._grid_frame.columnconfigure(c, weight=1, uniform="cols", minsize=size)
        radius = int(size * 0.25)
        for idx, btn in enumerate(self._buttons):
            r, c = divmod(idx, cols)
            btn.configure(width=size, height=size, corner_radius=radius)
            btn.grid_configure(row=r, column=c)

    def add_screenshot_button(
        self,
        img_path,                
        screenshot_entry: dict 
    ):
        new_cls     = screenshot_entry["classification"]
        fg, hover   = self.color_map.get(new_cls, ("dimgray", "gray"))
        fname = screenshot_entry["filename"]
        print(f"Adding new {new_cls} screenshot")

        on_task, off_task, none = self.get_totals()

        if (on_task + off_task + none) < 1:
            self.refresh() # Reinitialize
        else:
            self.data["screenshots"].append(screenshot_entry)

            if new_cls == "on-task":
                on_task += 1
            elif new_cls == "off-task":
                off_task += 1
            elif new_cls == "none":
                none += 1

            self.update_totals_display(on_task, off_task, none)

            btn = ctk.CTkButton(
                self._grid_frame,
                text="",
                fg_color=fg,
                hover_color=hover,
            )

            btn.configure(
                command=partial(
                    self.update_screenshot, 
                    btn, 
                    img_path,
                    screenshot_entry,
                    fname
                )
            )

            self._buttons.append(btn)
            btn.grid(padx=3, pady=3, sticky="nsew")
            
            # Call resize to configure grid
            self._on_frame_resize()

    def update_screenshot(self, button, image_path, screenshot_entry, fname):
        on_task, off_task, none = self.get_totals()
        cls = self.rev_color_map.get(button.cget("fg_color"))

        ts = datetime.strptime(fname.replace("screenshot_", "").replace(".png", ""),
                              "%Y%m%d_%H%M%S")
        time_label = ts.strftime("%-I:%M %p (%Y/%m/%d)")

        if cls == "on-task":
            on_task -= 1
        elif cls == "off-task":
            off_task -= 1
        elif cls == "none":
            none -= 1

        new_cls = self.classify_screenshot(image_path, self.json_path, screenshot_entry, time_label, False)

        if new_cls is not None: # No action taken
          new_cls = new_cls.lower()

          if new_cls == "on-task":
              on_task += 1
          elif new_cls == "off-task":
              off_task += 1
          elif new_cls == "none":
              none += 1
          
          print(f"Changed classification from {cls} to {new_cls}")

          if new_cls != "x": # Reclassify
            fg, hover = self.color_map.get(new_cls, ("dimgray", "gray"))
            button.configure(fg_color=fg, hover_color=hover)
            screenshot_entry["classification"] = new_cls

            for entry in self.data.get("screenshots", []):
                if entry["filename"] == screenshot_entry["filename"]:
                    entry["classification"] = new_cls

          else: # Remove
              button.destroy()
              self._buttons.remove(button)
              self._on_frame_resize()

              self.data["screenshots"] = [
                        entry for entry in self.data["screenshots"]
                        if entry["filename"] != screenshot_entry["filename"]
                    ]
            
          self.update_totals_display(on_task, off_task, none)

    def update_json_path(self, json_path, save_path):
        # Refresh the grid when switching days.
        self.json_path = json_path
        self.save_path = save_path

        self.refresh()

    def refresh(self):
        self.data = self.load_json()

        for child in self._grid_frame.grid_slaves():
            child.destroy()
        self.update_idletasks()
        print("About to create grid")
        self.create_squares_grid()

        on_task, off_task, none = self.get_totals()
        self.update_totals_display(on_task, off_task, none)