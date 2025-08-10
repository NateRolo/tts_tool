from openai import OpenAI
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import pygame
import platform
import ctypes
import time  # Added time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# --- DPI Awareness ---
if platform.system() == "Windows":
    try:
        # Try for Per-Monitor DPI Awareness V2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            # Try for Per-Monitor DPI Awareness V1
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            try:
                # Try for System DPI Awareness
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                print("Warning: Could not set DPI awareness. GUI might appear blurry on high-DPI displays.")

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OpenAI's base URL
OPENAI_BASE_URL = "https://api.openai.com/v1"

# --- Initialize OpenAI Client ---
# We configure the OpenAI client to point to OpenAI's API endpoint.
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

pygame.mixer.init()  # Initialize pygame mixer


def text_to_speech(text_input: str, output_filename: str = "speech_output.mp3", model: str = "tts-1", voice: str = "alloy"):
    """
    Converts text to speech using OpenAI's API.

    Args:
        text_input (str): The text to convert to speech.
        output_filename (str): The name of the file to save the audio to.
        model (str): The TTS model to use (e.g., "tts-1", "tts-1-hd").
        voice (str): The voice to use (e.g., "alloy", "echo", "fable", "onyx", "nova", "shimmer").

    Returns:
        Path: The path to the saved audio file, or None if an error occurred.
    """
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set. Please set it in the .env file.")
        return None

    speech_file_path = Path(__file__).parent / output_filename

    print(f"Attempting to generate speech for: \"{text_input}\"")
    print(f"Using OpenAI TTS with model: {model}, voice: {voice}")
    print(f"Saving to: {speech_file_path}")

    try:
        # Call OpenAI's /v1/audio/speech endpoint
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text_input
        )

        # Stream the audio content to a file
        response.stream_to_file(speech_file_path)
        print(f"Speech successfully saved to {speech_file_path}")
        return speech_file_path
    except Exception as e:
        print(f"An error occurred while generating speech: {e}")
        print("Please ensure that your OpenAI API key is valid, has TTS capabilities, and that the model and voice parameters are correct.")
        return None


def text_to_speech_gui(text_input: str, output_filename: str, model: str, voice: str, speed: float):
    """
    Converts text to speech using OpenAI's API, designed for GUI integration.

    Args:
        text_input (str): The text to convert to speech.
        output_filename (str): The name of the file to save the audio to.
        model (str): The TTS model to use.
        voice (str): The voice to use.
        speed (float): The playback speed.

    Returns:
        tuple[bool, str]: (success, message_or_filepath)
                          If success is True, message_or_filepath is the path to the audio file.
                          If success is False, message_or_filepath is an error message.
    """
    if not OPENAI_API_KEY:
        return False, "Error: OPENAI_API_KEY is not set."

    try:
        # Ensure output_filename is a full path if it's not already
        speech_file_path = Path(output_filename)
        if not speech_file_path.is_absolute():
            speech_file_path = Path(__file__).parent / output_filename
        speech_file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    except Exception as e:
        return False, f"Error creating speech file path: {e}"

    try:
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=text_input,
            speed=speed,
            response_format="mp3"
        ) as response:
            response.stream_to_file(speech_file_path)
        return True, str(speech_file_path)
    except Exception as e:
        return False, f"An error occurred while generating speech: {e}"


class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenAI Text-to-Speech Tool")
        self.root.geometry("800x700")  # Increased window size for better visibility

        self.current_filepath = None
        self.voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        self.models = ["tts-1", "tts-1-hd"]
        self.playback_state = "stopped"  # Can be "playing", "paused", "stopped"
        self.sound_object = None
        self.playback_start_time = 0
        self.paused_elapsed_time = 0  # To store elapsed time when paused

        self._create_widgets()
        self._check_api_key()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)  # Handle cleanup

    def _on_closing(self):
        if pygame.mixer.get_busy():
            pygame.mixer.stop()
        pygame.mixer.quit()
        self.root.destroy()

    def _check_api_key(self):
        if not OPENAI_API_KEY:
            self.status_var.set("Critical Error: Valid OPENAI_API_KEY is not configured in the .env file.")
            self.convert_button.config(state=tk.DISABLED)

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Top Controls Frame ---
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(3, weight=1)

        ttk.Label(controls_frame, text="Model:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_var = tk.StringVar(value=self.models[0])
        model_menu = ttk.OptionMenu(controls_frame, self.model_var, self.models[0], *self.models)
        model_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(controls_frame, text="Voice:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.voice_var = tk.StringVar(value=self.voices[0])
        voice_menu = ttk.OptionMenu(controls_frame, self.voice_var, self.voices[0], *self.voices)
        voice_menu.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(controls_frame, text="Speed:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(controls_frame, from_=0.25, to=4.0, variable=self.speed_var, orient=tk.HORIZONTAL, command=self._update_speed_label)
        speed_scale.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        self.speed_label_var = tk.StringVar(value="1.00x")
        ttk.Label(controls_frame, textvariable=self.speed_label_var).grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)

        # --- Text Input Frame ---
        text_frame = ttk.LabelFrame(main_frame, text="Input Text", padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.text_input = tk.Text(text_frame, wrap=tk.WORD, height=10, undo=True)
        self.text_input.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_input.yview)
        text_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.text_input.config(yscrollcommand=text_scrollbar.set)
        self.text_input.bind("<KeyRelease>", self._update_char_count)

        # --- Character Count Label ---
        self.char_count_var = tk.StringVar(value="Characters: 0 / 4096")
        self.char_count_label = ttk.Label(main_frame, textvariable=self.char_count_var)
        self.char_count_label.pack(fill=tk.X, padx=10, pady=(0, 10))

        # --- Output and Actions Frame ---
        output_actions_frame = ttk.LabelFrame(main_frame, text="Output & Actions", padding="10")
        output_actions_frame.pack(fill=tk.X)
        output_actions_frame.columnconfigure(1, weight=1)

        ttk.Label(output_actions_frame, text="Output File:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_file_var = tk.StringVar(value="speech_output.mp3")
        output_file_entry = ttk.Entry(output_actions_frame, textvariable=self.output_file_var)
        output_file_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        browse_button = ttk.Button(output_actions_frame, text="Browse...", command=self._browse_output_file)
        browse_button.grid(row=0, column=2, padx=5, pady=5)

        self.convert_button = ttk.Button(output_actions_frame, text="Convert to Speech", command=self._convert_tts_threaded)
        self.convert_button.grid(row=1, column=0, columnspan=2, padx=5, pady=10, sticky=tk.EW)

        # Playback Controls Frame
        playback_controls_frame = ttk.Frame(output_actions_frame)
        playback_controls_frame.grid(row=1, column=2, padx=5, pady=5, sticky=tk.EW)

        self.play_pause_button = ttk.Button(playback_controls_frame, text="Play", command=self._toggle_play_pause, state=tk.DISABLED)
        self.play_pause_button.pack(side=tk.LEFT, padx=(0, 2))

        self.stop_button = ttk.Button(playback_controls_frame, text="Stop", command=self._stop_audio, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        # --- Progress Bar ---
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(output_actions_frame, variable=self.progress_var, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.grid(row=2, column=0, columnspan=3, padx=5, pady=(10, 5), sticky=tk.EW)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready. Inspired by naturalreaders.com/online/")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="2")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _update_speed_label(self, value):
        self.speed_label_var.set(f"{float(value):.2f}x")

    def _update_char_count(self, event=None):
        char_count = len(self.text_input.get("1.0", tk.END).rstrip('\n'))
        self.char_count_var.set(f"Characters: {char_count} / 4096")
        if char_count > 4096:
            self.char_count_label.config(foreground="red")
            self.status_var.set("Warning: Character count exceeds 4096 limit!")
        else:
            self.char_count_label.config(foreground="")
            if not self.convert_button["text"] == "Converting...":
                if self.convert_button['state'] == tk.DISABLED and not self.status_var.get().startswith("Converting"):
                    self.convert_button.config(state=tk.NORMAL)
            if self.status_var.get().startswith("Warning: Character count"):
                self.status_var.set("Ready.")
        return char_count

    def _browse_output_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 audio", "*.mp3"), ("All files", "*.*")],
            initialfile=self.output_file_var.get() or "speech_output.mp3",
            title="Save Speech As"
        )
        if filename:
            self.output_file_var.set(filename)

    def _convert_tts_threaded(self):
        text = self.text_input.get("1.0", tk.END).strip()
        char_count = len(text)

        if char_count > 4096:
            messagebox.showerror("Character Limit Exceeded", f"The input text ({char_count} characters) exceeds the 4096 character limit for OpenAI TTS.")
            self.status_var.set(f"Error: Text too long ({char_count}/4096). Conversion cancelled.")
            self.char_count_label.config(foreground="red")
            return
        elif char_count == 0 and not text:
            messagebox.showwarning("Input Required", "Please enter some text to convert.")
            return

        self.char_count_label.config(foreground="")

        output_filename = self.output_file_var.get().strip()
        if not output_filename:
            messagebox.showwarning("Output Filename Required", "Please specify an output filename.")
            return

        model = self.model_var.get()
        voice = self.voice_var.get()
        speed = self.speed_var.get()

        self.status_var.set(f"Converting using {model}, {voice}, {speed:.2f}x speed...")
        self.convert_button.config(state=tk.DISABLED)
        self.play_pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

        thread = threading.Thread(target=self._perform_tts_conversion, args=(text, output_filename, model, voice, speed))
        thread.daemon = True
        thread.start()

    def _perform_tts_conversion(self, text, output_filename, model, voice, speed):
        success, result = text_to_speech_gui(text, output_filename, model, voice, speed)
        if success:
            self.current_filepath = result
            self.status_var.set(f"Speech saved to: {self.current_filepath}")
            self.play_pause_button.config(state=tk.NORMAL, text="Play")
            self.stop_button.config(state=tk.NORMAL)
            self.playback_state = "stopped"
            self.progress_bar.config(value=0)  # Reset progress bar
            if self.sound_object:
                self.sound_object = None
            self.char_count_label.config(foreground="")
        else:
            self.current_filepath = None
            self.status_var.set(f"Error: {result}")
            messagebox.showerror("Conversion Failed", result)

        self.convert_button.config(state=tk.NORMAL)
        self._update_char_count()

    def _toggle_play_pause(self):
        if not self.current_filepath:
            messagebox.showerror("Error", "No audio file to play. Convert text first.")
            return

        if self.playback_state == "stopped":
            try:
                if not self.sound_object:
                    self.sound_object = pygame.mixer.Sound(self.current_filepath)

                duration_sec = self.sound_object.get_length()
                self.progress_bar.config(maximum=duration_sec, value=0)
                self.paused_elapsed_time = 0  # Reset paused time

                self.sound_object.play()
                self.playback_start_time = time.time()  # Record start time
                self.playback_state = "playing"
                self.play_pause_button.config(text="Pause")
                self.status_var.set(f"Playing: {Path(self.current_filepath).name}")
                threading.Thread(target=self._monitor_playback, daemon=True).start()
            except pygame.error as e:
                messagebox.showerror("Playback Error", f"Could not play audio: {e}")
                self.status_var.set(f"Error playing audio: {e}")
                self.playback_state = "stopped"
                self.play_pause_button.config(text="Play")
                self.progress_bar.config(value=0)
        elif self.playback_state == "playing":
            pygame.mixer.pause()
            self.paused_elapsed_time = time.time() - self.playback_start_time + self.paused_elapsed_time
            self.playback_state = "paused"
            self.play_pause_button.config(text="Resume")
            self.status_var.set(f"Paused: {Path(self.current_filepath).name}")
        elif self.playback_state == "paused":
            pygame.mixer.unpause()
            self.playback_start_time = time.time()
            self.playback_state = "playing"
            self.play_pause_button.config(text="Pause")
            self.status_var.set(f"Resumed: {Path(self.current_filepath).name}")
            if not any(t.name == '_monitor_playback_thread' for t in threading.enumerate()):
                threading.Thread(target=self._monitor_playback, name='_monitor_playback_thread', daemon=True).start()

    def _stop_audio(self):
        if self.sound_object and pygame.mixer.get_busy():
            pygame.mixer.stop()
            self.sound_object = None
        self.playback_state = "stopped"
        self.play_pause_button.config(text="Play", state=tk.NORMAL if self.current_filepath else tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL if self.current_filepath else tk.DISABLED)
        self.progress_bar.config(value=0)  # Reset progress bar
        self.paused_elapsed_time = 0
        if self.current_filepath:
            self.status_var.set(f"Stopped. Ready to play: {Path(self.current_filepath).name}")
        else:
            self.status_var.set("Playback stopped.")

    def _monitor_playback(self):
        """Monitors if the sound has finished playing and updates progress."""
        while self.playback_state == "playing" and pygame.mixer.get_busy():
            current_elapsed_sec = (time.time() - self.playback_start_time) + self.paused_elapsed_time

            # Ensure value doesn't exceed maximum due to timing discrepancies
            max_val = self.progress_bar['maximum']
            current_elapsed_sec = min(current_elapsed_sec, max_val)

            self.root.after(0, self.progress_var.set, current_elapsed_sec)
            pygame.time.wait(50)  # Update roughly 20 times a second

        # If it stopped playing (and wasn't manually stopped or paused before loop exit)
        if self.playback_state == "playing" and not pygame.mixer.get_busy():
            self.root.after(0, self._playback_finished_gui_update)

    def _playback_finished_gui_update(self):
        """Updates GUI when playback finishes naturally."""
        if self.playback_state == "playing":  # Ensure it wasn't stopped/paused by user action
            self.playback_state = "stopped"
            self.play_pause_button.config(text="Play")
            self.progress_bar.config(value=self.progress_bar['maximum'])  # Ensure it fills up
            self.paused_elapsed_time = 0  # Reset for next play
            if self.current_filepath:
                self.status_var.set(f"Finished playing: {Path(self.current_filepath).name}. Ready to replay.")


def main_gui():
    """
    Main function to launch the TTS GUI.
    """
    if not OPENAI_API_KEY:
        print("Critical Error: OPENAI_API_KEY is not configured in the .env file.")
        root_check = tk.Tk()
        root_check.withdraw()
        messagebox.showerror("API Key Error", "OPENAI_API_KEY is not configured correctly in the .env file. Please add it and restart.")
        root_check.destroy()
        return

    root = tk.Tk()
    app = TTSApp(root)
    app._update_char_count()
    root.mainloop()


if __name__ == "__main__":
    main_gui()
