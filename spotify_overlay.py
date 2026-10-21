import tkinter as tk
import customtkinter as ctk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import urllib.request
from PIL import Image, ImageTk
import io
import threading
import time

# --- KONFIGURACJA API SPOTIFY ---
CLIENT_ID = 'cd2df583ea154994bd8a1420bae6253f'
CLIENT_SECRET = 'a136f64aeae24f22aeebebe3171e8f1f'
REDIRECT_URI = 'http://127.0.0.1:9090/callback'
SCOPE = 'user-read-currently-playing user-read-playback-state user-modify-playback-state'

# Ustawienia wyglądu
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class SpotifyOverlay(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ustawienia okna
        self.title("Spotify Mini")
        self.geometry("320x130")
        self.resizable(False, False)
        
        # Opcja ZAWSZE NA WIERZCHU
        self.attributes("-topmost", True)
        
        # Usuwamy klasyczną belkę okna (opcjonalnie, można odkomentować jak chcesz super minimalizm)
        # self.overrideredirect(True)

        self.sp = None
        self.current_track_id = None

        # Połączenie ze Spotify
        try:
            auth_manager = SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope=SCOPE
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            print(f"Błąd połączenia: {e}")

        # --- UI LAYOUT ---
        # Okładka
        self.cover_label = ctk.CTkLabel(self, text="", width=90, height=90, fg_color="#222222", corner_radius=8)
        self.cover_label.place(x=15, y=20)

        # Tytuł utworu
        self.title_label = ctk.CTkLabel(self, text="Łączenie ze Spotify...", font=("Arial", 13, "bold"), anchor="w", wraplength=190)
        self.title_label.place(x=115, y=20)

        # Wykonawca
        self.artist_label = ctk.CTkLabel(self, text="-", font=("Arial", 11), text_color="gray", anchor="w", wraplength=190)
        self.artist_label.place(x=115, y=45)

        # Przyciski sterowania
        self.btn_prev = ctk.CTkButton(self, text="⏮", width=40, height=30, command=self.prev_track, font=("Arial", 14))
        self.btn_prev.place(x=115, y=80)

        self.btn_play = ctk.CTkButton(self, text="⏯", width=50, height=30, command=self.play_pause, font=("Arial", 14), fg_color="#1DB954", hover_color="#1ed760")
        self.btn_play.place(x=162, y=80)

        self.btn_next = ctk.CTkButton(self, text="⏭", width=40, height=30, command=self.next_track, font=("Arial", 14))
        self.btn_next.place(x=219, y=80)

        # Wątek do automatycznego odświeżania informacji
        self.update_thread = threading.Thread(target=self.refresh_loop, daemon=True)
        self.update_thread.start()

    def refresh_loop(self):
        while True:
            self.update_track_info()
            time.sleep(2)  # odświeżanie co 2 sekundy

    def update_track_info(self):
        if not self.sp:
            return
        try:
            playback = self.sp.current_playback()
            if playback and playback.get('item'):
                track = playback['item']
                track_id = track['id']
                
                if track_id != self.current_track_id:
                    self.current_track_id = track_id
                    title = track['name']
                    artist = ", ".join([a['name'] for a in track['artists']])
                    cover_url = track['album']['images'][0]['url']

                    # Aktualizacja tekstu
                    self.title_label.configure(text=title)
                    self.artist_label.configure(text=artist)

                    # Pobranie okładki
                    raw_data = urllib.request.urlopen(cover_url).read()
                    image = Image.open(io.BytesIO(raw_data)).resize((90, 90), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=image, dark_image=image, size=(90, 90))
                    self.cover_label.configure(image=ctk_img, text="")
            else:
                self.title_label.configure(text="Brak odtwarzania")
                self.artist_label.configure(text="Włącz coś w Spotify")
        except Exception as e:
            pass

    def play_pause(self):
        try:
            playback = self.sp.current_playback()
            if playback and playback['is_playing']:
                self.sp.pause_playback()
            else:
                self.sp.start_playback()
            time.sleep(0.3)
            self.update_track_info()
        except: pass

    def next_track(self):
        try:
            self.sp.next_track()
            time.sleep(0.3)
            self.update_track_info()
        except: pass

    def prev_track(self):
        try:
            self.sp.previous_track()
            time.sleep(0.3)
            self.update_track_info()
        except: pass

if __name__ == "__main__":
    app = SpotifyOverlay()
    app.mainloop()