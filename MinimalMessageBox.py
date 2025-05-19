from PIL import Image
from typing import List, Optional, Dict
import customtkinter as ctk


class MinimalMessageBox(ctk.CTkToplevel):
    def __init__(
        self,
        master:     ctk.CTk | None = None,
        title:      str            = "Title",
        message:    str | None     = None,
        img_path:   str | None     = None,
        options:    List[Dict]     = None,
        font_scale: float          = 1.0
    ):
        super().__init__(master)

        if options is None:
            options = [{"label": "OK"}]
        self.font_scale = font_scale

        self.title(title)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._response: Optional[str] = None

        unit = 80

        frame = ctk.CTkFrame(self, corner_radius=8)
        frame.grid(padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        row = 0

        if message:
            msg_lbl = ctk.CTkLabel(frame, text=message, justify="center", wraplength=450, font=("", int(14 * self.font_scale)))
            msg_lbl.grid(row=row, column=0, pady=(12, 6), sticky="n")
            row += 1

        if img_path:
            try:
                pil = Image.open(img_path)
                w, h = pil.size
                max_w, max_h = 450, 300
                scale = min(max_w / w, max_h / h, 1)
                ctk_img = ctk.CTkImage(pil, size=(int(w * scale), int(h * scale)))
                img_lbl = ctk.CTkLabel(frame, image=ctk_img, text="")
                img_lbl.grid(row=row, column=0, pady=(8, 12), sticky="n")
                row += 1
            except Exception as e:
                print(f"[MinimalMessageBox] Could not load icon: {e}")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=row, column=0, pady=(6, 10))
        btn_frame.grid_columnconfigure(tuple(range(len(options))), weight=1)

        for idx, opt in enumerate(options):
            ratio = opt.get("width_ratio", 1)
            text = opt.get("display_label", opt["label"])
            b = ctk.CTkButton(
                btn_frame,
                text=text,
                font=("", int(14 * self.font_scale)),
                width=int(unit * ratio),
                fg_color=opt.get("color"),
                hover_color=opt.get("hover_color", opt.get("color")),
                command=lambda v=opt["label"]: self._on_select(v)
            )
            b.grid(row=0, column=idx, padx=6, ipadx=8)

        self.update_idletasks()
        w, h = max(self.winfo_width(), 250), max(self.winfo_height(), 150)

        if master:
            x = master.winfo_rootx() + (master.winfo_width() - w)//2
            y = master.winfo_rooty()  + (master.winfo_height() - h)//2
        else:
            x = (self.winfo_screenwidth() - w)//2
            y = (self.winfo_screenheight() - h)//2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.deiconify()
        self.wait_visibility()
        self.grab_set()

    def get(self) -> Optional[str]:
        self.wait_window(self)
        return self._response

    def _on_select(self, value: str):
        self._response = value
        self.destroy()

    def _on_close(self):
        self._response = None
        self.destroy()