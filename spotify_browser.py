import asyncio
import ctypes
import math
import os
import sys
import threading
import time
import tkinter as tk
import winsound
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageSequence, ImageTk
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
)
import pystray
from pystray import MenuItem as item

# Ustawienia wyglądu
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")


def resource_path(relative_path):
  try:
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")
  return os.path.join(base_path, relative_path)


class BrowserSpotifyOverlay(ctk.CTk):

  def __init__(self):
    super().__init__()

    # Okienko 380x100
    self.title("Web Spotify Mini")
    self.geometry("380x100")
    self.resizable(False, False)

    # Wyśrodkowanie u góry ekranu
    self.update_idletasks()
    screen_width = self.winfo_screenwidth()
    x = (screen_width - 380) // 2
    y = 15
    self.geometry(f"380x100+{x}+{y}")

    # Zawsze na wierzchu, bez ramki i półprzezroczyste
    self.attributes("-topmost", True)
    self.overrideredirect(True)
    self.attributes("-alpha", 0.95)

    # Fizyczne wycięcie rogów przez Win32 API
    self.after(10, self.apply_rounded_corners)

    self.full_title = "Oczekiwanie..."
    self.scroll_index = 0
    self.is_playing = False

    self.gif_frames = []
    self.dance_frames = []
    self.frame_index = 0

    self.load_gifs()

    self.protocol("WM_DELETE_WINDOW", self.hide_window)

    # --- GŁÓWNA RAMKA ---
    self.main_frame = ctk.CTkFrame(
        self,
        width=380,
        height=100,
        fg_color="#161616",
        corner_radius=16,
        border_width=2,
        border_color="#ff2a8d",
    )
    self.main_frame.place(x=0, y=0)

    # 1. Płyta winylowa po lewej
    self.cover_label = ctk.CTkLabel(
        self.main_frame, text="", width=76, height=76, fg_color="#161616"
    )
    self.cover_label.place(x=12, y=14)

    # 2. Tytuł utworu
    self.title_label = ctk.CTkLabel(
        self.main_frame,
        text=self.full_title,
        font=("Arial", 11, "bold"),
        text_color="#ffffff",
        anchor="center",
        width=182,
    )
    self.title_label.place(x=98, y=14)

    # 3. Wykonawca
    self.artist_label = ctk.CTkLabel(
        self.main_frame,
        text="Włącz coś w przeglądarce",
        font=("Arial", 10, "bold"),
        text_color="#1ed760",
        anchor="center",
        width=182,
    )
    self.artist_label.place(x=98, y=36)

    # 4. Przyciski sterujące
    btn_bg = "#222222"
    btn_hover = "#2a2a2a"

    self.btn_prev = ctk.CTkButton(
        self.main_frame,
        text="⏮",
        width=38,
        height=24,
        fg_color=btn_bg,
        hover_color=btn_hover,
        text_color="#ffffff",
        command=self.prev_track,
    )
    self.btn_prev.place(x=108, y=65)

    self.btn_play = ctk.CTkButton(
        self.main_frame,
        text="⏯",
        width=48,
        height=24,
        command=self.play_pause,
        fg_color="#1DB954",
        hover_color="#1ed760",
        text_color="#000000",
        font=("Arial", 12, "bold"),
    )
    self.btn_play.place(x=152, y=65)

    self.btn_next = ctk.CTkButton(
        self.main_frame,
        text="⏭",
        width=38,
        height=24,
        fg_color=btn_bg,
        hover_color=btn_hover,
        text_color="#ffffff",
        command=self.next_track,
    )
    self.btn_next.place(x=206, y=65)

    # 5. Tańcząca waifu po prawej
    self.dance_label = ctk.CTkLabel(
        self.main_frame, text="", width=76, height=76, fg_color="#161616"
    )
    self.dance_label.place(x=292, y=14)

    # Przycisk zamknięcia (✕)
    self.btn_close = ctk.CTkButton(
        self.main_frame,
        text="✕",
        width=22,
        height=22,
        fg_color="transparent",
        text_color="#aaaaaa",
        hover_color="#e81123",
        command=self.hide_window,
        font=("Arial", 10),
    )
    self.btn_close.place(x=350, y=8)

    # Przesuwanie okna myszką
    for widget in [
        self.main_frame,
        self.cover_label,
        self.title_label,
        self.artist_label,
        self.dance_label,
    ]:
      widget.bind("<Button-1>", self.start_move)
      widget.bind("<B1-Motion>", self.do_move)

    self.running = True
    threading.Thread(target=self.poll_media, daemon=True).start()
    threading.Thread(target=self.ticker_loop, daemon=True).start()

    self.animate_all()

    self.tray_icon = None
    self.setup_tray()

  def play_uwu_sound(self):
    try:
      sound_path = resource_path("uwu.wav")
      if os.path.exists(sound_path):
        winsound.PlaySound(
            sound_path, winsound.SND_ASYNC | winsound.SND_FILENAME
        )
    except Exception:
      pass

  def load_gifs(self):
    try:
      im = Image.open(resource_path("vinyl.gif"))
      for frame in ImageSequence.Iterator(im):
        f_res = frame.copy().resize((76, 76), Image.Resampling.LANCZOS)
        self.gif_frames.append(
            ctk.CTkImage(light_image=f_res, dark_image=f_res, size=(76, 76))
        )
    except Exception:
      img = Image.new("RGB", (76, 76), color="#121212")
      self.gif_frames.append(
          ctk.CTkImage(light_image=img, dark_image=img, size=(76, 76))
      )

    try:
      dance_mask = Image.new("L", (76, 76), 0)
      ImageDraw.Draw(dance_mask).rounded_rectangle(
          [0, 0, 76, 76], radius=12, fill=255
      )

      im_dance = Image.open(resource_path("dance.gif"))
      for frame in ImageSequence.Iterator(im_dance):
        f_res = (
            frame.copy().resize((76, 76), Image.Resampling.LANCZOS).convert("RGBA")
        )
        rounded_frame = Image.new("RGBA", (76, 76), (22, 22, 22, 255))
        rounded_frame.paste(f_res, (0, 0), dance_mask)

        self.dance_frames.append(
            ctk.CTkImage(
                light_image=rounded_frame,
                dark_image=rounded_frame,
                size=(76, 76),
            )
        )
    except Exception:
      img = Image.new("RGB", (76, 76), color="#121212")
      self.dance_frames.append(
          ctk.CTkImage(light_image=img, dark_image=img, size=(76, 76))
      )

  def animate_all(self):
    if self.running:
      colors = [
          (255, 42, 141),
          (157, 0, 255),
          (0, 100, 255),
          (0, 240, 255),
          (29, 185, 84),
      ]

      total_steps = 50
      idx = (self.frame_index % total_steps) / (total_steps / len(colors))
      i1 = int(idx) % len(colors)
      i2 = (i1 + 1) % len(colors)
      f = idx - int(idx)

      r = int(colors[i1][0] * (1 - f) + colors[i2][0] * f)
      g = int(colors[i1][1] * (1 - f) + colors[i2][1] * f)
      b = int(colors[i1][2] * (1 - f) + colors[i2][2] * f)

      color_hex = f"#{r:02x}{g:02x}{b:02x}"
      self.main_frame.configure(border_color=color_hex)

      if self.is_playing:
        self.frame_index = (self.frame_index + 1) % max(
            len(self.gif_frames), 1
        )
        if self.gif_frames:
          self.cover_label.configure(
              image=self.gif_frames[
                  self.frame_index % len(self.gif_frames)
              ]
          )
        if self.dance_frames:
          self.dance_label.configure(
              image=self.dance_frames[
                  self.frame_index % len(self.dance_frames)
              ]
          )
    self.after(50, self.animate_all)

  def apply_rounded_corners(self):
    try:
      hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
      if not hwnd:
        hwnd = self.winfo_id()
      w = self.winfo_width()
      h = self.winfo_height()
      rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w, h, 18, 18)
      ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)
    except Exception:
      pass

  def setup_tray(self):
    try:
      icon_path = resource_path("icon.png")
      image = Image.open(icon_path)
    except Exception:
      image = Image.new("RGB", (64, 64), color="#121212")
      dc = ImageDraw.Draw(image)
      dc.ellipse([8, 8, 56, 56], fill="#1DB954")

    menu = (
        item("Pokaż / Ukryj", self.toggle_window),
        item("Wyjdź", self.quit_app),
    )
    self.tray_icon = pystray.Icon(
        "SpotifyMini", image, "Spotify Mini Player", menu
    )
    threading.Thread(target=self.tray_icon.run, daemon=True).start()

  def hide_window(self):
    self.withdraw()

  def show_window(self):
    self.deiconify()
    self.attributes("-topmost", True)

  def toggle_window(self, icon, item):
    if self.winfo_viewable():
      self.withdraw()
    else:
      self.after(0, self.show_window)

  def quit_app(self, icon, item):
    self.running = False
    if self.tray_icon:
      self.tray_icon.stop()
    self.destroy()

  def start_move(self, event):
    self.x = event.x
    self.y = event.y

  def do_move(self, event):
    deltax = event.x - self.x
    deltay = event.y - self.y
    x = self.winfo_x() + deltax
    y = self.winfo_y() + deltay
    self.geometry(f"+{x}+{y}")

  def poll_media(self):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while self.running:
      try:
        loop.run_until_complete(self.update_media_info())
      except Exception:
        pass
      time.sleep(1)

  async def update_media_info(self):
    manager = await SessionManager.request_async()
    session = manager.get_current_session()
    if session:
      info = await session.try_get_media_properties_async()
      title = info.title if info and info.title else "Brak tytułu"
      artist = info.artist if info and info.artist else "Nieznany wykonawca"

      self.is_playing = True
      if title != self.full_title:
        self.full_title = title
        self.artist_label.configure(text=artist)
        self.scroll_index = 0
    else:
      self.full_title = "Brak aktywnego odtwarzacza"
      self.artist_label.configure(text="Włącz coś w przeglądarce")
      self.is_playing = False

  def ticker_loop(self):
    while self.running:
      # Zawsze animujemy tytuł, niezależnie od jego długości
      padded = self.full_title + "     •     "
      self.scroll_index = (self.scroll_index + 1) % len(padded)
      visible = (padded + padded)[self.scroll_index : self.scroll_index + 18]
      self.title_label.configure(text=visible)
      time.sleep(0.08)

  def play_pause(self):
    self.play_uwu_sound()
    asyncio.run(self._send_command("play_pause"))

  def next_track(self):
    self.play_uwu_sound()
    asyncio.run(self._send_command("next"))

  def prev_track(self):
    self.play_uwu_sound()
    asyncio.run(self._send_command("prev"))

  async def _send_command(self, cmd):
    manager = await SessionManager.request_async()
    session = manager.get_current_session()
    if session:
      if cmd == "play_pause":
        await session.try_toggle_play_pause_async()
      elif cmd == "next":
        await session.try_skip_next_async()
      elif cmd == "prev":
        await session.try_skip_previous_async()


if __name__ == "__main__":
  app = BrowserSpotifyOverlay()
  app.mainloop()