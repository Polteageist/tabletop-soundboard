import customtkinter
import json
import math
import pygame
import re
import shutil
import threading
import time
import tkinter
import yt_dlp
from tkinter import colorchooser, simpledialog
from copy import deepcopy
from CTkToolTip import CTkToolTip
from matplotlib import colors
from pathlib import Path
from PIL import ImageTk, Image
from pydub import AudioSegment
from pytablericons import TablerIcons, OutlineIcon
import sounddevice as sd
import io
import webbrowser

VERSION_NUM = "0.1.3"
FADE_DURATION = 2000
TRANSITION_INCREMENT = 0.02
HIGHLIGHT_BORDER_WIDTH = 4
BUTTON_WIDTH = 140

DEFAULT_COLOR = "#1C6BA4"
DEFAULT_COLOR_HOVER = "#23476D"
DEFAULT_COLOR_DISABLED = "#627E99"

ACCENT_COLOR = "#9264C0"
ACCENT_COLOR_HOVER = "#643B8D"
ACCENT_COLOR_DISABLED = "#9F80C0"

ydl_opts = {
	'format': 'bestaudio/best',
	'postprocessors': [{
		'key': 'FFmpegExtractAudio',
		'preferredcodec': 'mp3',
		'preferredquality': '192',
	}],
}

save_icon = customtkinter.CTkImage(light_image=TablerIcons.load(OutlineIcon.DEVICE_FLOPPY, color='#000'),
									dark_image=TablerIcons.load(OutlineIcon.DEVICE_FLOPPY, color='#fff'))
globe_icon = customtkinter.CTkImage(light_image=TablerIcons.load(OutlineIcon.WORLD, color='#000'),
									dark_image=TablerIcons.load(OutlineIcon.WORLD, color='#fff'))
edit_icon = customtkinter.CTkImage(light_image=TablerIcons.load(OutlineIcon.EDIT, color='#000'),
									dark_image=TablerIcons.load(OutlineIcon.EDIT, color='#fff'))

ICON_SIZE = 24

loop_icon = customtkinter.CTkImage(light_image=TablerIcons.load(OutlineIcon.REPEAT, color='#000', size=ICON_SIZE),
									dark_image=TablerIcons.load(OutlineIcon.REPEAT, color='#fff', size=ICON_SIZE))
playlist_icon = customtkinter.CTkImage(light_image=TablerIcons.load(OutlineIcon.PLAYLIST, color='#000', size=ICON_SIZE),
									dark_image=TablerIcons.load(OutlineIcon.PLAYLIST, color='#fff', size=ICON_SIZE))
fade_icon = customtkinter.CTkImage(light_image=TablerIcons.load(OutlineIcon.BLEND_MODE, color='#000', size=ICON_SIZE),
									dark_image=TablerIcons.load(OutlineIcon.BLEND_MODE, color='#fff', size=ICON_SIZE))
autosave_icon = customtkinter.CTkImage(light_image=TablerIcons.load(OutlineIcon.DEVICE_FLOPPY, color='#000', size=ICON_SIZE),
									dark_image=TablerIcons.load(OutlineIcon.DEVICE_FLOPPY, color='#fff', size=ICON_SIZE))

def make_bird():
	bird = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-canary">
        <path stroke="none" d="M0 0h24v24H0z" fill="none" />
        <path d="M12 20v-2" />
        <path d="M15 8.01v.01" />
        <path d="M3 17l8 -8v-1a4 4 0 1 1 8 0h2l-2 2v1a7 7 0 0 1 -13.215 3.223" />
</svg>'''
	svg_image = pygame.image.load(io.BytesIO(bird.encode()))
	image_bytes = pygame.image.tobytes(svg_image, 'RGBA')
	return Image.frombytes('RGBA', (24, 24), image_bytes)

bird_icon = customtkinter.CTkImage(light_image=make_bird())


try:
	with open('settings.json', 'r') as settings_file:
		settings = json.load(settings_file)
except FileNotFoundError:
	settings = {"autosave": False, "tooltips": True}
	with open('settings.json', 'w') as settings_file:
		json.dump(settings, settings_file, indent="\t")

try:
	pygame.mixer.init(devicename=settings["audioDevice"])
except:
	pygame.mixer.init()

sb_dir = (Path.cwd() / "Soundboards")
sb_dir.mkdir(exist_ok=True)
active_dir = None

if "activeDir" in settings:
	active_dir = sb_dir / settings["activeDir"]
	if not active_dir.is_dir():
		active_dir = None

if active_dir is None:
	for directory in sb_dir.iterdir():
		if directory.is_dir() and (directory / "data.json").is_file():
			active_dir = directory
			break

if active_dir is None:
	active_dir = sb_dir / "New Soundboard 1"
	active_dir.mkdir(exist_ok=True)

def initialize_data():
	global data, saved_data
	settings["activeDir"] = active_dir.name
	with open('settings.json', 'w') as settings_file:
		json.dump(settings, settings_file, indent="\t")
	try:
		with open(active_dir / 'data.json', 'r') as data_file:
			data = json.load(data_file)
	except FileNotFoundError:
		data = {
			"globalMusicVolume": 1.0,
			"globalAmbienceVolume": 0.5,
			"color": "#888888",
			"fade": False,
			"loop": True,
			"pages": [
				{
					"index": 0,
					"pageLabel": "Page 1",
					"columns": [
						{
							"index": 0,
							"columnLabel": "Add tracks in edit mode!",
							"tracks": []
						}
					]
				}
			]
		}
		with open(active_dir / 'data.json', 'w') as data_file:
			json.dump(data, data_file, indent="\t")

	saved_data = deepcopy(data)

def initialize_app():
	global audio, app

	try:
		app.close()
	except:
		pass

	audio = AudioManager()
	app = App(root)

	try:
		pygame.mixer.stop()
		pygame.mixer.music.stop()
		pygame.mixer.quit()
	except:
		pass

	try:
		pygame.mixer.init(devicename=settings["audioDevice"])
	except:
		pygame.mixer.init()

	app.default_loop = customtkinter.BooleanVar(value=data["loop"])
	app.fade_transitions = customtkinter.BooleanVar(value=data["fade"])
	fffdefdfdfdefdefdfdefffde49 = "beans"

def finalize_app():
	audio_monitor_handler = threading.Thread(target=audio.audio_monitor, daemon=True)
	app.set_tooltips()
	app.update_idletasks()
	audio_monitor_handler.start()
	app.config_header.update_icons()
	app.focus_force()

def open_soundboard(event):
	new_sb = tkinter.filedialog.askdirectory(initialdir=sb_dir, title="Select the soundboard folder to open")
	if not new_sb:
		return
	new_sb = Path(new_sb)

	if new_sb == sb_dir:
		tkinter.messagebox.showinfo("Error", "Please select a folder.")
		return
	elif not new_sb.is_relative_to(sb_dir):
		tkinter.messagebox.showinfo("Error", "Please select a folder in the Soundboards directory.")
		return

	load_new_soundboard(new_sb)

def new_soundboard(event):
	name = simpledialog.askstring(
		title="New Soundboard",
		prompt="Name new soundboard:"
	)
	if not name:
		return

	new_sb = sb_dir / name
	if new_sb.exists():
		tkinter.messagebox.showinfo("Error", "This soundboard already exists.")
		return
	else:
		try:
			new_sb.mkdir()
		except:
			tkinter.messagebox.showinfo("Error", "Soundboard could not be created.")
			return

	load_new_soundboard(new_sb)

def load_new_soundboard(new_sb):
	global active_dir
	if data != saved_data:
		match tkinter.messagebox.askyesnocancel(title="Save Changes?", message="Would you like to save your changes?"):
			case True:
				with open(active_dir / 'data.json', 'w') as data_file:
					json.dump(data, data_file, indent="\t")
			case False:
				pass
			case _:
				return

	active_dir = new_sb

	initialize_data()
	initialize_app()
	finalize_app()

def text_color(bg):
	rgb = colors.to_rgb(bg)
	luminance = math.sqrt( (0.299*(rgb[0]**2)) + (0.587*(rgb[1]**2)) + (0.114*(rgb[2]**2)) )
	return "white" if luminance < 0.5 else "black"

def hover_color(bg):
	hsv = colors.rgb_to_hsv(colors.to_rgb(bg))
	darkened = (hsv[0], hsv[1], max(0.0, hsv[2] - 0.1))
	return colors.to_hex(colors.hsv_to_rgb(darkened))

def disabled_color(bg):
	hsv = colors.rgb_to_hsv(colors.to_rgb(bg))
	lightened = (hsv[0], hsv[1], min(1.0, hsv[2] + 0.1))
	return colors.to_hex(colors.hsv_to_rgb(lightened))

def format_text(text):
	max_len = 14
	if len(text) > max_len:
		start = 0
		end = start + max_len
		while start < len(text) and end < len(text):
			space_idx = text.rfind(" ", start, end)
			if space_idx > -1:
				text = text[0:space_idx] + "\n" + text[space_idx + 1:]
				start = space_idx + 1
			else:
				text = text[0:end] + "\n" + text[end:]
				start = end
			end = start + max_len
	return text


class AudioManager():
	def __init__(self):
		self.playing_data = None
		self.main_started_playing = False
		self.ambience_data = None
		self.sfx_started_playing = False
		self.queue_data = None
		self.bookmark_data = None
		self.fade_queue_data = None
		self.fading = False
		self.temp_volume_cache = None
		self.main_backup_vol = None
		self.ambience_backup_vol = None
		self.channels = [pygame.mixer.Channel(x) for x in range(0, pygame.mixer.get_num_channels())]
		self.active_channel = self.channels[0]
		self.active_channel_track_idx = None
		self.close_audio_thread = False

	def audio_monitor(self):
		while not self.close_audio_thread:
			time.sleep(0.05)

			for c in self.channels:
				v = c.get_volume()
				if v < 1 and c is self.active_channel:
					c.set_volume(min(1, v + TRANSITION_INCREMENT))
				elif v > 0 and c is not self.active_channel:
					c.set_volume(max(0, v - TRANSITION_INCREMENT))

			main_busy = self.active_channel.get_busy()

			if not main_busy and self.fade_queue_data is not None:
				self.play_audio(*self.fade_queue_data)

			if main_busy and not self.main_started_playing:
				self.main_started_playing = True

			if self.playing_data is not None and self.main_started_playing and not main_busy:
				self.main_started_playing = False
				if self.queue_data is not None:
					if playlist_mode.get() and self.bookmark_data is None:
						self.bookmark_data = self.playing_data
					self.play_audio(*self.queue_data)
					continue

				if playlist_mode.get():
					if self.bookmark_data is not None:
						self.playing_data = self.bookmark_data
						self.bookmark_data = None
					next_track = self.find_next_track(self.playing_data[0], self.playing_data[1]["index"], self.playing_data[2]["index"])
					if next_track is None:
						self.playing_data = None
						app.disable_stop_music()
						if app.alternate_track_frame is not None:
							app.after_idle(lambda a=app.alternate_track_frame: app.destroy_atf(a))
					else:
						self.play_audio(*next_track)

				else:
					self.bookmark_data = None
					loop = self.playing_data[2]["loop"] if "loop" in self.playing_data[2] else data["loop"]
					if loop:
						self.play_audio(*self.playing_data, continue_loop=True)
					else:
						self.playing_data = None
						app.disable_stop_music()
						if app.alternate_track_frame is not None:
							app.after_idle(lambda a=app.alternate_track_frame: app.destroy_atf(a))

			sfx_busy = pygame.mixer.music.get_busy()
			if sfx_busy and not self.sfx_started_playing:
				self.sfx_started_playing = True

			if self.ambience_data is not None and self.sfx_started_playing and not sfx_busy:
				self.sfx_started_playing = False
				loop = self.ambience_data[2]["loop"] if "loop" in self.ambience_data[2] else data["loop"]
				if loop:
					self.play_audio(*self.ambience_data)
				else:
					self.ambience_data = None
					app.disable_stop_ambience()

	def find_next_track(self, page, col_index, row_index):
		visited_cols = []
		found_result = None
		for c in page["columns"]:
			for r in c["tracks"]:
				if "file" not in r:
					continue
				if "ambience" in r and r["ambience"]:
					continue
				if (c["index"] == col_index and r["index"] > row_index) or c["index"] > col_index:
					return (page, c, r)
				else:
					if found_result is None:
						found_result = (page, c, r)
		return found_result

	def play_audio(self, page, column, track, continue_loop=False):
		args = (page, column, track)

		self.queue_data = None
		volume = track["volume"] if "volume" in track else 1
		if self.temp_volume_cache is not None and args[self.temp_volume_cache[0]] is self.temp_volume_cache[1]:
			volume = self.temp_volume_cache[2]
		ambience = track["ambience"] if "ambience" in track else False

		if not ambience and data["fade"] and not self.fading and self.active_channel.get_busy():
			pygame.mixer.fadeout(FADE_DURATION)
			self.fade_queue_data = args
			self.fading = True

			if self.playing_data is not None:
				app.toggle_button_state(self.playing_data, "stop")
				app.color_current_page(self.playing_data[0], "dehighlight")

		else:
			self.fading = False
			if not ambience:
				if self.playing_data is not None:
					app.toggle_button_state(self.playing_data, "stop")
					app.color_current_page(self.playing_data[0], "dehighlight")

				self.fade_queue_data = None
				self.playing_data = None
				volume = self.calc_volume(volume, ambience)
				self.main_backup_vol = volume
				app.enable_stop_music()

				channel_dict = {}
				if app.alternate_track_frame is not None and continue_loop:
					channel_dict = app.alternate_track_frame.channel_dict
				else:
					self.active_channel = self.channels[0]
					channel_dict = {track["file"]: self.channels[0]}
					if "subdata" in track and len(track["subdata"]) > 1:
						c_id = 1
						for subdata_entry in track["subdata"]:
							if "file" not in subdata_entry:
								self.active_channel_track_idx = subdata_entry["subindex"]
								continue
							channel_dict[subdata_entry["file"]] = self.channels[c_id]
							c_id += 1
						app.load_atf(track, channel_dict)
						app.alternate_track_frame.buttons[self.active_channel_track_idx].configure(border_width=2, fg_color=ACCENT_COLOR_DISABLED, state="disabled")
					elif app.alternate_track_frame is not None:
						app.after_idle(lambda a=app.alternate_track_frame: app.destroy_atf(a))

				sound_dict = {}
				for filename in channel_dict:
					sound = pygame.mixer.Sound(str(active_dir / filename))
					sound.set_volume(volume)
					sound_dict[filename] = sound

				pygame.mixer.stop()
				for c in self.channels:
					c.set_volume(1 if c is self.active_channel else 0)

				self.main_started_playing = False
				self.playing_data = args
				app.color_current_page(self.playing_data[0], "highlight")
				app.toggle_button_state(self.playing_data, "play")

				pygame.mixer.pause()
				for filename, channel in channel_dict.items():
					channel.play(sound_dict[filename])
				pygame.mixer.unpause()

			else:
				pygame.mixer.music.load(str(active_dir / track["file"]))
				volume = self.calc_volume(volume, ambience)
				pygame.mixer.music.set_volume(volume)
				app.enable_stop_ambience()

				app.toggle_button_state(self.ambience_data, "stop")
				self.ambience_backup_vol = volume
				self.ambience_data = None
				pygame.mixer.music.stop()
				self.sfx_started_playing = False
				self.ambience_data = args
				app.toggle_button_state(self.ambience_data, "play")

				pygame.mixer.music.play()

	def stop_music(self, force_instant=False):
		if self.playing_data is not None:
			app.color_current_page(self.playing_data[0], "dehighlight")
			app.toggle_button_state(self.playing_data, "stop")

		self.playing_data = None
		self.queue_data = None
		self.bookmark_data = None
		self.fade_queue_data = None
		app.disable_stop_music()
		if force_instant or not data["fade"] or self.fading:
			self.fading = False
			pygame.mixer.stop()
			if app.alternate_track_frame is not None:
				app.after_idle(lambda a=app.alternate_track_frame: app.destroy_atf(a))
		else:
			pygame.mixer.fadeout(FADE_DURATION)
			self.fading = True
			if app.alternate_track_frame is not None:
				app.after_idle(lambda a=app.alternate_track_frame: app.destroy_atf(a))
		self.main_started_playing = False

	def stop_ambience(self, force_instant=False):
		if self.ambience_data is not None:
			app.toggle_button_state(self.ambience_data, "stop")

		self.ambience_data = None
		app.disable_stop_ambience()
		if not data["fade"] or force_instant:
			pygame.mixer.music.stop()
		else:
			pygame.mixer.music.fadeout(FADE_DURATION)
		self.sfx_started_playing = False

	def calc_volume(self, value, sfx, temp_global_volume=None):
		global_volume = data["globalMusicVolume"] if not sfx else data["globalAmbienceVolume"]
		global_volume = temp_global_volume if temp_global_volume is not None else global_volume
		return (global_volume * value / 2) ** 2

	def set_volume(self, value, sfx=False, save=True, absolute=False, temp_global_volume=None):
		if not absolute:
			value = self.calc_volume(value, sfx, temp_global_volume=temp_global_volume)
		if not sfx:
			if save:
				self.main_backup_vol = value
			for c in self.channels:
				if c.get_busy():
					c.get_sound().set_volume(value)
		else:
			if save:
				self.ambience_backup_vol = value
			if pygame.mixer.music.get_busy():
				pygame.mixer.music.set_volume(value)

	def clear_queue(self):
		self.queue_data = None

	def set_active_channel(self, channel, track):
		self.active_channel = channel
		self.active_channel_track_idx = track["subindex"]
		app.toggle_atf_buttons()



class App(customtkinter.CTkToplevel):
	def __init__(self, master):
		super().__init__()
		self.all_tooltips = []
		self.edit_mode = False
		self.edit_mode_add_objects = []

		self.title(f"Tabletop Soundboard {VERSION_NUM}")
		self.geometry("1280x720")
		self.grid_columnconfigure(1, weight=1)
		self.grid_rowconfigure(1, weight=1)

		self.config_header = ConfigHeader(self)
		self.config_header.grid(row=0, column=2, padx=(0, 10), pady=(10, 0), sticky="ne")
		self.add_header_tooltips()

		self.header = None
		self.load_header()

		self.page_view = None
		self.load_page(data["pages"][0])

		self.alternate_track_frame = None

		self.protocol("WM_DELETE_WINDOW", self.kill)
		self.bind("<Command-o>", open_soundboard)
		self.bind("<Control-o>", open_soundboard)
		self.bind("<Command-n>", new_soundboard)
		self.bind("<Control-n>", new_soundboard)
		self.bind("<Configure>", self.resize)

		self.bird_spot = customtkinter.CTkFrame(self)
		self.bird_spot.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="new")
		self.bird = customtkinter.CTkButton(self.bird_spot, text="", image=bird_icon, fg_color=ACCENT_COLOR, hover_color=ACCENT_COLOR_HOVER, width=32, height=32, command=lambda : webbrowser.open("https://www.youtube.com/watch?v=0iVlSNpq8i8"))
		self.bird.grid(row=0, column=0, padx=16, pady=14)

	def load_header(self):
		new_header = Header(self)
		if (bird.get()):
			new_header.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="ew")
		else:
			new_header.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="ew")
		if self.header is not None:
			self.after_idle(lambda h=self.header: self.destroy_header(h))
		self.header = new_header

		if audio.playing_data is None:
			self.disable_stop_music()
		else:
			self.color_current_page(audio.playing_data[0], "highlight")
		if audio.ambience_data is None:
			self.disable_stop_ambience()
		if hasattr(self, 'page_view') and self.page_view is not None:
			self.color_current_page(self.page_view.page_data)

		self.update_idletasks()

	def destroy_header(self, to_destroy):
		# to_destroy.global_settings_button.tooltip.destroy()
		# to_destroy.edit_button.tooltip.destroy()
		# if hasattr(to_destroy, "save_button"):
		# 	to_destroy.save_button.tooltip.destroy()
		to_destroy.destroy()

	def load_page(self, page_data):
		new_page = PageView(self, page_data)
		new_page.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
		if self.page_view is not None:
			self.after_idle(lambda p=self.page_view: self.destroy_page(p))
		self.page_view = new_page
		self.update_idletasks()
		self.add_page_tooltips()
		if self.edit_mode:
			self.enable_page_edit_mode()

		self.color_current_page(page_data)
		self.toggle_button_state(audio.playing_data, "play")
		self.toggle_button_state(audio.ambience_data, "play")

	def destroy_page(self, to_destroy):
		self.color_current_page(to_destroy.page_data, "inactive")

		for c in to_destroy.columns:
			for t in c.entries:
				if hasattr(t, "tooltip"):
					t.tooltip.destroy()
		to_destroy.destroy()

	def color_current_page(self, page_data, command="active"):
			start_index = 2 if self.uses_ambience() else 1
			if command == "active":
				self.header.header_buttons[start_index+page_data["index"]].configure(state="disabled", fg_color=ACCENT_COLOR)
			elif command == "inactive":
				self.header.header_buttons[start_index+page_data["index"]].configure(state="normal", fg_color=DEFAULT_COLOR)
			elif command == "highlight":
				self.header.header_buttons[start_index+page_data["index"]].configure(border_width=2)
			elif command == "dehighlight":
				self.header.header_buttons[start_index+page_data["index"]].configure(border_width=0)

	def destroy_object_tooltip(self, to_destroy):
		if hasattr(to_destroy, "tooltip"):
			to_destroy.tooltip.destroy()
		to_destroy.destroy()

	def load_atf(self, track_data, channel_dict):
		new_frame = AlternateTrackFrame(self, track_data, channel_dict)
		new_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
		if self.alternate_track_frame is not None:
			self.after_idle(lambda a=self.alternate_track_frame: self.destroy_atf(a))
		self.alternate_track_frame = new_frame
		self.after_idle(self.add_atf_tooltips)

		if audio.playing_data:
			self.toggle_atf_buttons()

	def destroy_atf(self, to_destroy):
		for b in to_destroy.buttons:
			if hasattr(b, "tooltip"):
				b.tooltip.destroy()
		to_destroy.destroy()

	def toggle_atf_buttons(self):
		tracks = self.alternate_track_frame.track_data["subdata"]
		for idx, c_button in enumerate(app.alternate_track_frame.buttons):
			if idx == audio.active_channel_track_idx:
				c_button.configure(
					fg_color=DEFAULT_COLOR_DISABLED if "file" in tracks[idx] else ACCENT_COLOR_DISABLED,
					border_width=2,
					state="disabled")
			else:
				c_button.configure(
					fg_color=DEFAULT_COLOR if "file" in tracks[idx] else ACCENT_COLOR,
					border_width=0,
					state="normal")

	def resize(self, event):
		self.header_grid()
		self.page_view_grid()
		self.atf_grid()

	def header_grid(self):
		header_width = self.header.winfo_width()
		button_width = self.header.stop_music_button.winfo_width()
		row_total = 12
		cols = 0
		while row_total + button_width + 20 <= header_width and cols < len(self.header.header_buttons):
			row_total += button_width + 20
			cols += 1
		cols = max(cols, 1)
		for i, button in enumerate(self.header.header_buttons):
			button.grid(row=i // cols, column=i % cols, pady=16 if i // cols == 0 else (0,16))

	def page_view_grid(self):
		if self.page_view is None:
			return
		if len(self.page_view.columns) == 0:
			return
		all_frames = self.page_view.columns.copy()
		if self.page_view.add_column_frame is not None:
			all_frames.append(self.page_view.add_column_frame)
		page_width = self.page_view.winfo_width()
		col_width = all_frames[0].winfo_width()
		row_total = 6
		cols = 0
		while row_total + col_width <= page_width and cols < len(all_frames):
			row_total += col_width
			cols += 1
		cols = max(cols, 1)
		for i, column in enumerate(all_frames):
			column.grid(row=i // cols, column=i % cols)
		self.page_view.grid_columnconfigure(tuple(range(cols)), uniform="columns")

	def atf_grid(self):
		if self.alternate_track_frame is None:
			return
		if not self.alternate_track_frame.winfo_exists():
			self.alternate_track_frame = None
			return
		
		atf_width = self.alternate_track_frame.winfo_width()
		button_width = self.alternate_track_frame.buttons[0].winfo_width()
		row_total = 12
		cols = 0
		while row_total + button_width + 20 <= atf_width and cols < len(self.alternate_track_frame.buttons):
			row_total += button_width + 20
			cols += 1
		cols = max(cols, 1)
		for i, button in enumerate(self.alternate_track_frame.buttons):
			button.grid(row=i // cols, column=i % cols, pady=16 if i // cols == 0 else (0,16))

	def data_changed(self):
		print(data)
		if settings["autosave"]:
			self.save()
		else:
			if self.get_save_button_state() == "normal":
				self.config_header.save_button.configure(
					state="normal",
					fg_color=DEFAULT_COLOR,
					hover_color=DEFAULT_COLOR_HOVER,
					border_color="#FFFFFF"
				)
			else:
				self.config_header.save_button.configure(
					state="disabled",
					fg_color=DEFAULT_COLOR_DISABLED,
					border_color=DEFAULT_COLOR_DISABLED
				)

	def get_save_button_state(self):
		return "disabled" if data == saved_data else "normal"

	def uses_ambience(self):
		for p in data["pages"]:
			for c in p["columns"]:
				for t in c["tracks"]:
					if "ambience" in t and t["ambience"]:
						return True
		return False

	def enable_stop_music(self):
		self.header.stop_music_button.configure(state="normal", fg_color=DEFAULT_COLOR)

	def enable_stop_ambience(self):
		if hasattr(self.header, "stop_ambience_button"):
			self.header.stop_ambience_button.configure(state="normal", fg_color=DEFAULT_COLOR)

	def disable_stop_music(self):
		self.header.stop_music_button.configure(state="disabled", fg_color=DEFAULT_COLOR_DISABLED)

	def disable_stop_ambience(self):
		if hasattr(self.header, "stop_ambience_button"):
			self.header.stop_ambience_button.configure(state="disabled", fg_color=DEFAULT_COLOR_DISABLED)

	def toggle_button_state(self, playing_data, state):
		if playing_data is not None:
			# if the song is on the current page. which it hopefully should be but just in case
			if playing_data[0]["index"] == self.page_view.page_data["index"]:
				song_button = self.page_view.columns[playing_data[1]["index"]].entries[playing_data[2]["index"]]
				if state == "play":
					song_button.configure(state="disabled", border_width=2)
				elif state == "stop":
					song_button.configure(state="normal", border_width=0)

	def reindex_pages(self):
		for i, page in enumerate(data["pages"]):
			page["index"] = i
		data["pages"].sort(key=lambda x: x["index"])
		app.data_changed()
		self.load_header()

	def global_settings(self, event):
		context_menu = tkinter.Menu(app, tearoff=0)

		context_menu.add_command(label="Global Music Volume", command=self.change_global_music_volume)
		context_menu.add_command(label="Global Ambience Volume", command=self.change_global_ambience_volume)
		context_menu.add_command(label="Change Default Color", command=self.change_default_color)
		context_menu.add_checkbutton(label="Show Track Counts", variable=show_track_count, command=self.toggle_track_count)
		context_menu.add_checkbutton(label="Use Fade Transitions", variable=self.fade_transitions, command=self.toggle_fade_transitions)
		context_menu.add_checkbutton(label="Loop by Default", variable=self.default_loop, command=self.toggle_default_loop)
		context_menu.add_separator()
		context_menu.add_checkbutton(label="Autosave", variable=autosave, command=self.toggle_autosave)
		context_menu.add_checkbutton(label="Enable Tooltips", variable=enable_tooltips, command=self.set_tooltips)
		context_menu.add_checkbutton(label="Playlist Mode", variable=playlist_mode, command=app.config_header.update_icons)
		context_menu.add_checkbutton(label="Bird", variable=bird, command=self.toggle_bird)
		context_menu.add_separator()

		audio_output_menu = tkinter.Menu(context_menu, tearoff=0)
		audio_output_menu.add_radiobutton(label="Default", variable=audio_device_var, value="DEFAULT", command=self.set_audio_output)
		devices = sd.query_devices()
		for device in devices:
			if device["max_output_channels"] > 0:
				audio_output_menu.add_radiobutton(label=device["name"], variable=audio_device_var, value=device["name"], command=self.set_audio_output)

		context_menu.add_cascade(label="Audio Output", menu=audio_output_menu)

		try:
			context_menu.post(event.x_root, event.y_root)
		finally:
			context_menu.grab_release()

	def toggle_track_count(self):
		self.load_page(self.page_view.page_data)
		self.load_header()

	def toggle_fade_transitions(self):
		data["fade"] = self.fade_transitions.get()
		self.config_header.update_icons()
		self.data_changed()

	def toggle_bird(self):
		self.load_header()

	def change_global_music_volume(self):
		audio.temp_volume_cache = None
		VolumePopup(app, self.receive_global_music_volume, data["globalMusicVolume"], global_volume_modifier="bgm")

	def receive_global_music_volume(self, value):
		data["globalMusicVolume"] = value
		if audio.playing_data is not None:
			audio.set_volume(audio.playing_data[2]["volume"] if "volume" in audio.playing_data[2] else 1)
		app.data_changed()

	def change_global_ambience_volume(self):
		audio.temp_volume_cache = None
		VolumePopup(app, self.receive_global_ambience_volume, data["globalAmbienceVolume"], global_volume_modifier="sfx")

	def receive_global_ambience_volume(self, value):
		data["globalAmbienceVolume"] = value
		if audio.ambience_data is not None:
			audio.set_volume(audio.ambience_data[2]["volume"] if "volume" in audio.ambience_data[2] else 1, sfx=True)
		app.data_changed()

	def change_default_color(self):
		color = colorchooser.askcolor()[1]
		if color is not None:
			data["color"] = color

			if self.page_view is not None:
				for c in self.page_view.columns:
					for button in c.entries:
						if not isinstance(button, customtkinter.CTkButton):
							continue
						if "color" not in button.track_data:
							button.configure(fg_color=data["color"], hover_color=hover_color(data["color"]), text_color=text_color(data["color"]))
			self.data_changed()

	def toggle_default_loop(self):
		data["loop"] = self.default_loop.get()
		if self.page_view is not None:
			for c in self.page_view.columns:
				for button in c.entries:
					if not isinstance(button, customtkinter.CTkButton):
						continue
					if "loop" not in button.track_data:
						button.loop_var.set(data["loop"])
		self.config_header.update_icons()
		self.data_changed()

	def toggle_autosave(self):
		if settings["autosave"] != autosave.get():
			settings["autosave"] = autosave.get()
			with open('settings.json', 'w') as settings_file:
				json.dump(settings, settings_file, indent="\t")
		if settings["autosave"]:
			self.save()
		self.config_header.update_icons()
		self.load_header()

	def set_tooltips(self):
		self.clear_tooltips()
		if settings["tooltips"] != enable_tooltips.get():
			settings["tooltips"] = enable_tooltips.get()
			with open('settings.json', 'w') as settings_file:
				json.dump(settings, settings_file, indent="\t")
		if settings["tooltips"]:
			self.add_header_tooltips()
			self.add_page_tooltips()
			self.add_atf_tooltips()

	def clear_tooltips(self):
		for tooltip in self.all_tooltips:
			tooltip.destroy()
		self.all_tooltips = []

	def add_header_tooltips(self):
		self.config_header.global_settings_button.tooltip = CTkToolTip(self.config_header.global_settings_button, message="Global settings", delay=1, follow=False)
		self.all_tooltips.append(self.config_header.global_settings_button.tooltip)
		self.config_header.edit_button.tooltip = CTkToolTip(self.config_header.edit_button, message="Edit mode", delay=1, follow=False)
		self.all_tooltips.append(self.config_header.edit_button.tooltip)
		if hasattr(self.config_header, "save_button"):
			self.config_header.save_button.tooltip = CTkToolTip(self.config_header.save_button, message="Save changes", delay=1, follow=False)
			self.all_tooltips.append(self.config_header.save_button.tooltip)

	def add_page_tooltips(self):
		if self.page_view is not None:
			for c in self.page_view.columns:
				for button in c.entries:
					if not isinstance(button, customtkinter.CTkButton):
						continue
					button.tooltip = CTkToolTip(button, message=Path(button.track_data["file"]).stem, delay=2, follow=False)
					self.all_tooltips.append(button.tooltip)

	def add_atf_tooltips(self):
		if self.alternate_track_frame is not None:
			for button in self.alternate_track_frame.buttons:
				button.tooltip = CTkToolTip(button, message=Path(button.file).stem, delay=2, follow=False)
				self.all_tooltips.append(button.tooltip)

	def set_audio_output(self):
		pygame.mixer.quit()
		output = audio_device_var.get()
		try:
			pygame.mixer.init(devicename=output)
			settings["audioDevice"] = output
		except:
			audio_device_var.set("DEFAULT")
			pygame.mixer.init()
			settings.pop("audioDevice", None)
		with open('settings.json', 'w') as settings_file:
			json.dump(settings, settings_file, indent="\t")

	def toggle_edit(self):
		self.edit_mode = not self.edit_mode
		self.load_header()
		if self.edit_mode:
			self.enable_page_edit_mode()
		else:
			if self.page_view is not None:
				for c in self.page_view.columns:
					for button in c.entries:
						if not isinstance(button, customtkinter.CTkButton):
							continue
						button.configure(state="normal")
						button.unbind("<Button-1>")
						button.unbind("<B1-Motion>")
			for obj in self.edit_mode_add_objects:
				obj.destroy()
			self.page_view.add_column_frame = None
			self.edit_mode_add_objects = []
			self.config_header.edit_button.configure(border_width=0, border_spacing=2)

			self.toggle_button_state(audio.playing_data, "play")
			self.toggle_button_state(audio.ambience_data, "play")

	def enable_page_edit_mode(self):
		if self.page_view is None:
			return
		self.config_header.edit_button.configure(border_width=2, border_spacing=0)
		for obj in self.edit_mode_add_objects:
			obj.destroy()
		self.page_view.add_column_frame = None
		self.edit_mode_add_objects = []
		for c in self.page_view.columns:
			for button in c.entries:
				if not isinstance(button, customtkinter.CTkButton):
					continue
				# button.configure(state="disabled")
				# button.bind("<Button-1>", lambda event, b=button: self.track_drag_start(event, b))
				# button.bind("<B1-Motion>", lambda event, b=button: self.track_drag_motion(event, b))
			add_button = customtkinter.CTkButton(c, text="Add Track")
			add_button.configure(command=lambda c=c, b=add_button: self.edit_add_track(c, b))
			add_button.grid(row=len(c.entries)+1, column=0, padx=10, pady=10, sticky="ew")
			self.edit_mode_add_objects.append(add_button)
		self.page_view.add_column_frame = customtkinter.CTkFrame(self.page_view)
		self.page_view.add_column_frame.grid(row=0, column=len(self.page_view.columns), padx=0, pady=0, sticky="new")
		self.page_view.add_column_frame.grid_columnconfigure(0, weight=1)
		add_column_button = customtkinter.CTkButton(self.page_view.add_column_frame, text="Add Column", command=self.edit_add_column)
		add_column_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
		self.edit_mode_add_objects.append(self.page_view.add_column_frame)

	# def track_drag_start(self, event, button):
	# 	button.startX = event.x
	# 	button.startY = event.y

	# def track_drag_motion(self, event, button):
	# 	x = button.winfo_x() - button.startX + event.x
	# 	y = button.winfo_y() - button.startY + event.y
	# 	button.place(x=x, y=y)

	def edit_add_track(self, column, add_button):
		self.select_audio_files(self.process_add_tracks, column, add_button)

	def select_audio_files(self, callback, *args, return_list=True):
		try:
			clipboard = app.clipboard_get().strip()
			youtube_regex = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([\w-]{11})'
			if re.match(youtube_regex, clipboard):
				if tkinter.messagebox.askyesno("Use YouTube Link?", "The soundboard found a YouTube link on your clipboard. Would you like to import it as an audio track?"):
					threading.Thread(target=self.import_youtube_track, args=(clipboard, callback, *args), daemon=True).start()
					return
		except tkinter.TclError:
			pass
		if return_list:
			callback(customtkinter.filedialog.askopenfilenames(
				filetypes=(("Audio files", "*.wav *.mp3 *.ogg *.flac *.m4a *.opus"), ("All files", "*.*"))
			), *args)
		else:
			callback(customtkinter.filedialog.askopenfilename(
				filetypes=(("Audio files", "*.wav *.mp3 *.ogg *.flac *.m4a *.opus"), ("All files", "*.*"))
			), *args)

	def import_youtube_track(self, clipboard, callback, *args):
		popup = LoadingPopup(app)
		with yt_dlp.YoutubeDL(ydl_opts | {'outtmpl': str(active_dir / '%(title)s.%(ext)s')}) as ydl:
			try:
				result = ydl.extract_info(clipboard, download=True)
				popup.destroy()
				app.clipboard_clear()
			except:
				popup.destroy()
				tkinter.messagebox.showinfo("Download Error", "The download could not be completed. Please try again.")
				return
		callback([result["requested_downloads"][0]["filepath"]], *args)

	def process_add_tracks(self, filenames, column, add_button):
		for filename in filenames:
			path = self.setup_file_path(filename)
			new_track_data = {"index": len(column.entries), "file": path.name}
			column.tracks.append(new_track_data)
			button = column.create_button(new_track_data)
			if settings["tooltips"]:
				button.tooltip = CTkToolTip(button, message=Path(button.track_data["file"]).stem, delay=2, follow=False)
				self.all_tooltips.append(button.tooltip)
			add_button.grid(row=len(column.entries)+1)
		self.data_changed()
		if len(filenames) == 1:
			column.change_text_volume(button)

	def setup_file_path(self, filename):
		path = Path(filename)
		if path.suffix == ".m4a":
			new_path = active_dir / f"{Path(filename).stem}.mp3"
			if not new_path.is_file():
				m4a = AudioSegment.from_file(path, format="m4a")
				m4a.export(new_path, format="mp3")
			path = new_path
		elif not (active_dir / Path(filename).name).is_file():
			path = active_dir / Path(filename).name
			shutil.copy(filename, active_dir)
		return path

	def edit_add_column(self):
		label = simpledialog.askstring(
			title="Set Column Label",
			prompt="Write label:"
		)
		if not label:
			return
		new_column_data = {"index": len(self.page_view.columns), "columnLabel": label, "tracks": []}
		self.page_view.page_data["columns"].append(new_column_data)
		column = self.page_view.create_column(new_column_data)
		self.enable_page_edit_mode()
		self.data_changed()

	def edit_add_page(self):
		label = simpledialog.askstring(
			title="Set Page Title",
			prompt="Write title:"
		)
		if not label:
			return
		new_page_data = {"index": len(data["pages"]), "pageLabel": label, "columns": []}
		data["pages"].append(new_page_data)
		self.load_header()
		self.load_page(new_page_data)
		self.data_changed()

	def save(self):
		global saved_data
		with open(active_dir / 'data.json', 'w') as data_file:
			json.dump(data, data_file, indent="\t")
		saved_data = deepcopy(data)
		if hasattr(self.config_header, "save_button"):
			self.config_header.save_button.configure(state="disabled", fg_color=DEFAULT_COLOR_DISABLED, border_color=DEFAULT_COLOR_DISABLED)

	def close(self):
		audio.close_audio_thread = True
		self.clear_tooltips()
		self.destroy()

	def kill(self):
		self.close()
		root.destroy()

class ConfigIcons(customtkinter.CTkFrame):
	def __init__(self, master):
		super().__init__(master)

		self.configure(fg_color="transparent")

		self.loop_label = customtkinter.CTkLabel(self, text="", height=9)
		self.loop_label.grid(row=0, column=0, padx=1, pady=1)

		self.fade_label = customtkinter.CTkLabel(self, text="", height=9)
		self.fade_label.grid(row=1, column=0, padx=1, pady=1)

		self.playlist_label = customtkinter.CTkLabel(self, text="", height=9)
		self.playlist_label.grid(row=0, column=1, padx=1, pady=1)

		self.save_label = customtkinter.CTkLabel(self, text="", height=9)
		self.save_label.grid(row=1, column=1, padx=1, pady=1)

		self.update_icons()


	def update_icons(self):
		exists = False
		
		if hasattr(self.master.master, 'default_loop') and self.master.master.default_loop.get():
			self.loop_label.configure(image=loop_icon)
			exists = True
		else:
			self.loop_label.configure(image="")
		
		if hasattr(self.master.master, 'fade_transitions') and self.master.master.fade_transitions.get():
			self.fade_label.configure(image=fade_icon)
			exists = True
		else:
			self.fade_label.configure(image="")
		
		if 'autosave' in globals() and autosave.get():
			self.save_label.configure(image=autosave_icon)
			exists = True
		else:
			self.save_label.configure(image="")

		if 'playlist_mode' in globals() and playlist_mode.get():
			self.playlist_label.configure(image=playlist_icon)
			exists = True
		else:
			self.playlist_label.configure(image="")

		if exists:
			self.grid(padx=(11,0))
		else:
			self.grid(padx=0)


class ConfigHeader(customtkinter.CTkFrame):
	def __init__(self, master):
		super().__init__(master)

		self.config_icons = ConfigIcons(self)
		self.config_icons.grid(row=0, column=0, pady=(8), sticky="ne")

		self.global_settings_button = customtkinter.CTkButton(self, text="", image=globe_icon, width=32, height=32, command=lambda: None)
		self.global_settings_button.bind("<Button-1>", self.master.global_settings)
		self.global_settings_button.grid(row=0, column=1, padx=(12,4), pady=14, sticky="nse")

		self.edit_button = customtkinter.CTkButton(
			self,
			text="",
			image=edit_icon,
			border_color="#FFFFFF",
			border_width = 0,
			width=32,
			height=32,
			command=self.master.toggle_edit)
		self.edit_button.grid(row=0, column=2, padx=(12,4), pady=14, sticky="nse")

		if not settings["autosave"]:
			
			self.save_button = customtkinter.CTkButton(
				self,
				text="",
				state=self.master.get_save_button_state(),
				image=save_icon,
				fg_color=DEFAULT_COLOR_DISABLED,
				border_color=DEFAULT_COLOR_DISABLED,
				border_width = 2,
				width=32,
				height=32,
				command=self.master.save)
			self.save_button.grid(row=0, column=3, padx=(12, 16), pady=14, sticky="nse")

	def update_icons(self):
		self.config_icons.update_icons()


class Header(customtkinter.CTkFrame):
	def __init__(self, master):
		super().__init__(master)

		self.header_buttons = []

		self.stop_music_button = customtkinter.CTkButton(self, 
			text="Stop Music",
			state="normal" if audio.playing_data is not None else "disabled",
			fg_color=DEFAULT_COLOR if audio.playing_data is not None else DEFAULT_COLOR_DISABLED,
			text_color_disabled="#D4D4D4",
			width=BUTTON_WIDTH,
			command=audio.stop_music)
		self.stop_music_button.grid(row=0, column=len(self.header_buttons), padx=(16,4), pady=16, sticky="ns")
		self.header_buttons.append(self.stop_music_button)

		if self.master.uses_ambience():
			self.stop_ambience_button = customtkinter.CTkButton(self,
				text="Stop Ambience",
				state="normal" if audio.ambience_data is not None else "disabled",
				fg_color=DEFAULT_COLOR if audio.playing_data is not None else DEFAULT_COLOR_DISABLED,
				text_color_disabled="#D4D4D4",
				width=BUTTON_WIDTH,
				command=audio.stop_ambience)
			self.stop_ambience_button.grid(row=0, column=len(self.header_buttons), padx=(16,4), pady=16, sticky="ns")
			self.header_buttons.append(self.stop_ambience_button)

		for i, page in enumerate(data["pages"]):
			label = page["pageLabel"]

			if show_track_count.get():
				track_count = 0
				for col in page["columns"]:
					track_count = track_count + len(col["tracks"])

				label = f"{label} ({track_count})"

			button = customtkinter.CTkButton(
				self, text=format_text(label),
				text_color_disabled="#D4D4D4",
				border_color="#FFFFFF",
				width=BUTTON_WIDTH,
				command=lambda a=data["pages"][i]: app.load_page(a))
			button.page_data = data["pages"][i]
			button.grid(row=0, column=len(self.header_buttons), padx=(16,4), pady=16, sticky="ns")
			button.bind("<Button-2>", lambda event, b=button: self.page_header_right_click_menu(event, b))
			button.bind("<Button-3>", lambda event, b=button: self.page_header_right_click_menu(event, b))
			self.header_buttons.append(button)

		if self.master.edit_mode:
			button = customtkinter.CTkButton(self, text="Add Page", command=app.edit_add_page)
			button.grid(row=0, column=len(self.header_buttons), padx=(16,4), pady=16, sticky="ns")
			self.header_buttons.append(button)


		self.grid_columnconfigure(tuple(range(len(self.header_buttons))), uniform="header_buttons")

	def page_header_right_click_menu(self, event, button):
		context_menu = tkinter.Menu(app, tearoff=0)

		enable_color_reset = False
		enable_volume_reset = False
		contains_non_ambient = False
		contains_non_loop = False
		has_tracks = False
		for c in button.page_data["columns"]:
			for t in c["tracks"]:
				has_tracks = True
				if "file" not in t:
					continue
				if "ambience" not in t or not t["ambience"]:
					contains_non_ambient = True
				if ("loop" in t and not t["loop"]) or ("loop" not in t and not data["loop"]):
					contains_non_loop = True
				if "color" in t:
					enable_color_reset = True
				if "volume" in t and t["volume"] != 1.0:
					enable_volume_reset = True
		context_menu.add_command(label="Change Page Title", command=lambda b=button: self.rename_page(b))
		context_menu.add_command(label="Overwrite Page Volume Settings", state="normal" if has_tracks else "disabled", command=lambda b=button: self.change_all_volume(b))
		context_menu.add_command(label="Overwrite Page Colors", state="normal" if has_tracks else "disabled", command=lambda b=button: self.change_all_colors(b))
		if contains_non_loop or not has_tracks:
			context_menu.add_command(label="Mark Page as Loopable", state="normal" if has_tracks else "disabled", command=lambda b=button: self.mark_all_loop(b))
		else:
			context_menu.add_command(label="Mark Page as Non-Loopable", state="normal" if has_tracks else "disabled", command=lambda b=button: self.mark_all_non_loop(b))
		if contains_non_ambient or not has_tracks:
			context_menu.add_command(label="Mark Page as Ambience", state="normal" if has_tracks else "disabled", command=lambda b=button: self.mark_all_ambient(b))
		else:
			context_menu.add_command(label="Mark Page as Music", state="normal" if has_tracks else "disabled", command=lambda b=button: self.mark_all_non_ambient(b))
		context_menu.add_separator()
		context_menu.add_command(label="Move Left", state="normal" if data["pages"][0] is not button.page_data else "disabled", command=lambda b=button: self.move_page_left(b))
		context_menu.add_command(label="Move Right", state="normal" if data["pages"][-1] is not button.page_data else "disabled", command=lambda b=button: self.move_page_right(b))
		context_menu.add_separator()
		context_menu.add_command(label="Reset Page Volume Settings", state="normal" if enable_volume_reset else "disabled", command=lambda b=button: self.reset_all_volume(b))
		context_menu.add_command(label="Reset Page Colors", state="normal" if enable_color_reset else "disabled", command=lambda b=button: self.reset_all_colors(b))
		context_menu.add_command(label="Remove Page", command=lambda b=button: self.remove_page(b))
		try:
			context_menu.post(event.x_root, event.y_root)
		finally:
			context_menu.grab_release()

	def rename_page(self, button):
		label = simpledialog.askstring(
			title="Change Page Title",
			prompt="Write new title:"
		)
		if not label:
			return
		
		button.page_data["pageLabel"] = label

		if show_track_count.get():
			track_count = 0
			for col in button.page_data["columns"]:
				track_count = track_count + len(col["tracks"])

			label = f"{label} ({track_count})"

		button.configure(text=format_text(label))

		app.data_changed()

	def change_all_volume(self, button):
		initial_vol = 1.0
		found = False
		if audio.playing_data is not None and audio.playing_data[0] is button.page_data:
			if "volume" in audio.playing_data[2]:
				initial_vol = audio.playing_data[2]["volume"]
		elif audio.ambience_data is not None and audio.ambience_data[0] is button.page_data:
			if "volume" in audio.ambience_data[2]:
				initial_vol = audio.ambience_data[2]["volume"]
		else:
			for c in button.page_data["columns"]:
				for t in c["tracks"]:
					if "file" in t:
						if "volume" in t:
							initial_vol = t["volume"]
						found = True
						break
				if found:
					break
		audio.temp_volume_cache = [0, button.page_data, initial_vol]
		VolumePopup(app, self.receive_page_volume, initial_vol, callback_param=button)

	def receive_page_volume(self, value, button):
		for c in button.page_data["columns"]:
			for t in c["tracks"]:
				if "file" not in t:
					continue
				t["volume"] = value
		if audio.playing_data is not None and audio.playing_data[0] is button.page_data:
			audio.set_volume(value)
		if audio.ambience_data is not None and audio.ambience_data[0] is button.page_data:
			audio.set_volume(value, sfx=True)
		app.data_changed()

	def change_all_colors(self, button):
		color = colorchooser.askcolor()[1]
		if color is not None:
			if app.page_view.page_data is button.page_data:
				for c in app.page_view.columns:
					for b in c.entries:
						if not isinstance(b, customtkinter.CTkButton):
							continue
						b.configure(fg_color=color, hover_color=hover_color(color), text_color=text_color(color))
						b.track_data["color"] = color
			else:
				for c in button.page_data["columns"]:
					for t in c["tracks"]:
						t["color"] = color
			app.data_changed()

	def mark_all_loop(self, button):
		if app.page_view.page_data is button.page_data:
			for c in app.page_view.columns:
				for b in c.entries:
					if not isinstance(b, customtkinter.CTkButton):
						continue
					b.loop_var.set(True)
					if data["loop"]:
						b.track_data.pop("loop", None)
					else:
						b.track_data["loop"] = True
		else:
			for c in button.page_data["columns"]:
				for t in c["tracks"]:
					if data["loop"]:
						t.pop("loop", None)
					else:
						t["loop"] = True
		app.data_changed()

	def mark_all_non_loop(self, button):
		if app.page_view.page_data is button.page_data:
			for c in app.page_view.columns:
				for b in c.entries:
					if not isinstance(b, customtkinter.CTkButton):
						continue
					b.loop_var.set(False)
					if data["loop"]:
						b.track_data["loop"] = False
					else:
						b.track_data.pop("loop", None)
		else:
			for c in button.page_data["columns"]:
				for t in c["tracks"]:
					if data["loop"]:
						t["loop"] = False
					else:
						t.pop("loop", None)
		app.data_changed()

	def mark_all_ambient(self, button):
		u = app.uses_ambience()
		if audio.playing_data is not None and audio.playing_data[0] is button.page_data:
			audio.stop_music()
		if app.page_view.page_data is button.page_data:
			for c in app.page_view.columns:
				for b in c.entries:
					if not isinstance(b, customtkinter.CTkButton):
						continue
					b.ambience_var.set(True)
					b.track_data["ambience"] = True
		else:
			for c in button.page_data["columns"]:
				for t in c["tracks"]:
					t["ambience"] = True
		app.data_changed()
		if u != app.uses_ambience():
			app.load_header()

	def mark_all_non_ambient(self, button):
		u = app.uses_ambience()
		if audio.ambience_data is not None and audio.ambience_data[0] is button.page_data:
			audio.stop_ambience()
		if app.page_view.page_data is button.page_data:
			for c in app.page_view.columns:
				for b in c.entries:
					if not isinstance(b, customtkinter.CTkButton):
						continue
					b.ambience_var.set(False)
					b.track_data.pop("ambience", None)
		else:
			for c in button.page_data["columns"]:
				for t in c["tracks"]:
					t.pop("ambience", None)
		app.data_changed()
		if u != app.uses_ambience():
			app.load_header()

	def move_page_left(self, button):
		index = data["pages"].index(button.page_data)
		data["pages"].insert(index - 1, data["pages"].pop(index))
		app.reindex_pages()

	def move_page_right(self, button):
		index = data["pages"].index(button.page_data)
		data["pages"].insert(index + 1, data["pages"].pop(index))
		app.reindex_pages()

	def reset_all_volume(self, button):
		if audio.playing_data is not None and audio.playing_data[0] is button.page_data:
			audio.set_volume(1)
		if audio.ambience_data is not None and audio.ambience_data[0] is button.page_data:
			audio.set_volume(1, sfx=True)
		for c in button.page_data["columns"]:
			for t in c["tracks"]:
				t.pop("volume", None)
		app.data_changed()

	def reset_all_colors(self, button):
		if app.page_view.page_data is button.page_data:
			for c in app.page_view.columns:
				for b in c.entries:
					if not isinstance(b, customtkinter.CTkButton):
						continue
					b.configure(fg_color=data["color"], hover_color=hover_color(data["color"]), text_color=text_color(data["color"]))
					b.track_data.pop("color", None)
		else:
			for c in button.page_data["columns"]:
				for t in c["tracks"]:
					t.pop("color", None)
		app.data_changed()

	def remove_page(self, button):
		if audio.playing_data is not None and audio.playing_data[0] is button.page_data:
			audio.stop_music()
		if audio.ambience_data is not None and audio.ambience_data[0] is button.page_data:
			audio.stop_ambience()
		preferred_index = button.page_data["index"]
		queue_new_page = app.page_view.page_data is button.page_data
		data["pages"].remove(button.page_data)
		app.reindex_pages()
		if queue_new_page:
			if len(data["pages"]) <= 0:
				app.destroy_page(app.page_view)
				app.page_view = None
			else:
				index = min(preferred_index, len(data["pages"]) - 1)
				app.load_page(data["pages"][index])



class PageView(customtkinter.CTkScrollableFrame):
	def __init__(self, master, page_data):
		super().__init__(master)
		self.page_data = page_data
		self.columns = []
		self.add_column_frame = None

		for column_data in page_data["columns"]:
			self.create_column(column_data)

	def create_column(self, column_data):
		column = Column(self, column_data)
		column.grid(row=0, column=len(self.columns), padx=0, pady=0, sticky="new")
		self.columns.append(column)

	def reindex_columns(self):
		for i, column in enumerate(self.columns):
			column.column_data["index"] = i
			column.grid(column=i)
		self.page_data["columns"].sort(key=lambda x: x["index"])
		app.data_changed()



class Column(customtkinter.CTkFrame):
	def __init__(self, master, column_data):
		super().__init__(master)
		self.column_data = column_data
		self.tracks = column_data["tracks"]

		self.grid_columnconfigure(0, weight=1)

		self.title = customtkinter.CTkButton(self,
			text=format_text(column_data["columnLabel"]),
			fg_color="gray30",
			text_color_disabled="#FFF",
			width=BUTTON_WIDTH,
			state="disabled")
		self.title.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
		self.title.bind("<Button-2>", self.column_label_right_click_menu)
		self.title.bind("<Button-3>", self.column_label_right_click_menu)

		self.entries = []

		for track_data in self.tracks:
			if "file" not in track_data:
				blank = self.create_blank(track_data["index"]+1, track_data)
				self.entries.append(blank)
				continue
			self.create_button(track_data)

	def create_button(self, track_data):
		label = track_data["label"] if "label" in track_data else Path(track_data["file"]).stem
		color = track_data["color"] if "color" in track_data else data["color"]
		loop = track_data["loop"] if "loop" in track_data else data["loop"]
		ambience = track_data["ambience"] if "ambience" in track_data else False
		highlight = track_data["highlight"] if "highlight" in track_data else False
		disabled = False

		if show_track_count.get() and "subdata" in track_data:
			label = f"{label} ({len(track_data["subdata"])})"

		# try:
		# 	disabled = app.edit_mode
		# except:
		# 	disabled = False
		button = customtkinter.CTkButton(
			self,
			text=format_text(label),
			fg_color=color, 
			hover_color=hover_color(color), 
			text_color=text_color(color),
			border_color="white", 
			border_width=0,
			text_color_disabled=text_color(color),
			width=BUTTON_WIDTH,
			state="disabled" if disabled else "normal",
			)
		if highlight:
			button.configure(font=highlight_font)
		button.configure(command=lambda b=button: threading.Thread(
			target=self.play_audio_button, args=(self.master.page_data, self.column_data, b.track_data), daemon=True).start())
		button.grid(row=track_data["index"]+1, column=0, padx=10, pady=10, sticky="ew")
		button.track_data = track_data
		button.loop_var = customtkinter.BooleanVar(value=loop)
		button.highlight_var = customtkinter.BooleanVar(value=highlight)
		button.ambience_var = customtkinter.BooleanVar(value=ambience)
		button.bind("<Button-2>", lambda event, b=button: self.button_right_click_menu(event, b))
		button.bind("<Button-3>", lambda event, b=button: self.button_right_click_menu(event, b))
		self.entries.append(button)
		return button

	def create_blank(self, row, track_data):
		blank = customtkinter.CTkLabel(self, text="", fg_color="transparent")
		blank.track_data = track_data
		blank.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
		blank.bind("<Button-2>", lambda event, b=blank: self.blank_right_click_menu(event, b))
		blank.bind("<Button-3>", lambda event, b=blank: self.blank_right_click_menu(event, b))
		return blank

	def reindex_tracks(self):
		for i, entry in enumerate(self.entries):
			entry.track_data["index"] = i
			entry.grid(row=i+1)
		self.tracks.sort(key=lambda x: x["index"])
		app.data_changed()

	def play_audio_button(self, page, column, track):
		audio.queue_data = None
		audio.bookmark_data = None
		audio.play_audio(page, column, track)

	def button_right_click_menu(self, event, button):
		context_menu = tkinter.Menu(app, tearoff=0)

		uses_upper_segment = False
		if (
			("ambience" not in button.track_data or not button.track_data["ambience"]) and
			(audio.queue_data is None or audio.queue_data[2] is not button.track_data) and
			audio.playing_data is not None and
			(audio.playing_data[2] is not button.track_data or playlist_mode.get() or not (button.track_data["loop"] if "loop" in button.track_data else data["loop"]))
		):
			context_menu.add_command(label="Queue Track", command=lambda b=button: self.queue_track(b))
			uses_upper_segment = True
		if audio.queue_data is not None and (audio.queue_data[2] is button.track_data or (audio.playing_data is not None and audio.playing_data[2] is button.track_data)):
			context_menu.add_command(label="Clear Queue", command=audio.clear_queue)
			uses_upper_segment = True
		if uses_upper_segment:
			context_menu.add_separator()
		context_menu.add_command(label="Change Label/Volume", command=lambda b=button: self.change_text_volume(b))
		context_menu.add_command(label="Change Color", command=lambda b=button: self.change_color(b))
		context_menu.add_checkbutton(label="Loop Track", variable=button.loop_var, command=lambda b=button: self.toggle_loop(b))
		context_menu.add_checkbutton(label="Ambience", variable=button.ambience_var, command=lambda b=button: self.toggle_ambience(b))
		context_menu.add_checkbutton(label="Highlight", variable=button.highlight_var, command=lambda b=button: self.toggle_highlight(b))
		context_menu.add_command(label="Link Alternate Track", state="normal" if ("ambience" not in button.track_data or not button.track_data["ambience"]) and
			not ("subdata" in button.track_data and len(button.track_data["subdata"]) >= 8) else "disabled", command=lambda b=button: self.link_alternate_track(b))
		context_menu.add_separator()
		context_menu.add_command(label="Move Up", state="normal" if self.entries[0] is not button else "disabled", command=lambda b=button: self.move_track_up(b))
		context_menu.add_command(label="Move Down", state="normal" if self.entries[-1] is not button else "disabled", command=lambda b=button: self.move_track_down(b))
		context_menu.add_command(label="Add Blank Space Below", state="normal" if self.entries[-1] is not button else "disabled",
			command=lambda b=button: self.add_blank_space_below(b))
		context_menu.add_separator()
		context_menu.add_command(label="Reset Label", state="normal" if "label" in button.track_data else "disabled", command=lambda b=button: self.reset_text(b))
		context_menu.add_command(label="Reset Color", state="normal" if "color" in button.track_data else "disabled", command=lambda b=button: self.reset_color(b))
		context_menu.add_command(label="Reset Alternate Tracks", state="normal" if "subdata" in button.track_data else "disabled",
			command=lambda b=button: self.reset_alternate_tracks(b))
		context_menu.add_command(label="Remove Track", command=lambda b=button: self.remove_track(b))
		try:
			context_menu.post(event.x_root, event.y_root)
		finally:
			context_menu.grab_release()

	def queue_track(self, button):
		d = (self.master.page_data, self.column_data, button.track_data)
		if "ambience" not in button.track_data or not button.track_data["ambience"]:
			if audio.playing_data is None:
				audio.play_audio(d)
			else:
				audio.queue_data = d

	def change_text_volume(self, button):
		initial_vol = button.track_data["volume"] if "volume" in button.track_data else 1
		audio.temp_volume_cache = [2, button.track_data, initial_vol]
		TextVolumePopup(app, self.receive_text_volume, button, self, initial_vol)

	def receive_text_volume(self, button, new_label, new_volume):
		if new_label:
			text = new_label
			if show_track_count.get() and "subdata" in button.track_data:
				text = f"{new_label} ({len(button.track_data["subdata"])})"
			button.configure(text=format_text(text))
			button.track_data["label"] = new_label
		button.track_data["volume"] = new_volume
		if audio.playing_data is not None and audio.playing_data[2] is button.track_data:
			audio.set_volume(new_volume)
		if audio.ambience_data is not None and audio.ambience_data[2] is button.track_data:
			audio.set_volume(new_volume, sfx=True)
		app.data_changed()

	def change_color(self, button):
		color = colorchooser.askcolor()[1]
		if color is not None:
			button.configure(fg_color=color, hover_color=hover_color(color), text_color=text_color(color))
			button.track_data["color"] = color
			app.data_changed()

	def toggle_loop(self, button):
		if button.loop_var.get() == data["loop"]:
			button.track_data.pop("loop", None)
		else:
			button.track_data["loop"] = button.loop_var.get()
		app.data_changed()

	def toggle_ambience(self, button):
		u = app.uses_ambience()
		if button.ambience_var.get():
			button.track_data["ambience"] = True
			if audio.playing_data is not None and audio.playing_data[2] is button.track_data:
				audio.stop_music()
		else:
			button.track_data.pop("ambience", None)
			if audio.ambience_data is not None and audio.ambience_data[2] is button.track_data:
				audio.stop_ambience()
		app.data_changed()
		if u != app.uses_ambience():
			app.load_header()

	def toggle_highlight(self, button):
		if button.highlight_var.get():
			button.track_data["highlight"] = True
			button.configure(font=highlight_font)
		else:
			button.track_data.pop("highlight", None)
			button.configure(font=normal_font)
		app.data_changed()

	def link_alternate_track(self, button):
		app.select_audio_files(self.process_alternate_track, button, return_list=False)

	def move_track_up(self, button):
		index = self.entries.index(button)
		self.entries.insert(index - 1, self.entries.pop(index))
		self.reindex_tracks()

	def move_track_down(self, button):
		index = self.entries.index(button)
		self.entries.insert(index + 1, self.entries.pop(index))
		self.reindex_tracks()

	def add_blank_space_below(self, button):
		index = button.track_data["index"] + 1
		new_data = {}
		self.tracks.insert(index, new_data)
		blank = self.create_blank(index+1, new_data)
		self.entries.insert(index, blank)
		self.reindex_tracks()

	def process_alternate_track(self, filename, button):
		if "subdata" not in button.track_data:
			button.track_data["subdata"] = [{"subindex": 0, "sublabel": "Default"}]
		path = app.setup_file_path(filename)
		label = simpledialog.askstring(
			title="Label Alternate Track",
			prompt="Write label:"
		)
		if not label:
			label = path.stem
		button.track_data["subdata"].append({"file": path.name, "subindex": len(button.track_data["subdata"]), "sublabel": label})

		label = button.track_data["label"] if "label" in button.track_data else Path(button.track_data["file"]).stem
		button.configure(text=label if "subdata" not in button.track_data else f"{label} ({len(button.track_data["subdata"])})")

		app.data_changed()

	def reset_text(self, button):
		button.configure(text=Path(button.track_data["file"]).stem)
		button.track_data.pop("label", None)
		app.data_changed()

	def reset_color(self, button):
		button.configure(fg_color=data["color"], hover_color=hover_color(data["color"]), text_color=text_color(data["color"]))
		button.track_data.pop("color", None)
		app.data_changed()

	def reset_alternate_tracks(self, button):
		if audio.playing_data is not None and audio.playing_data[2] is button.track_data:
			audio.set_active_channel(audio.channels[0])
			if app.alternate_track_frame is not None:
				app.after_idle(lambda a=app.alternate_track_frame: app.destroy_atf(a))
		button.track_data.pop("subdata", None)

		label = button.track_data["label"] if "label" in button.track_data else Path(button.track_data["file"]).stem
		button.configure(text=label)

		app.data_changed()

	def remove_track(self, button):
		if audio.playing_data is not None and audio.playing_data[2] is button.track_data:
			audio.stop_music()
		if audio.ambience_data is not None and audio.ambience_data[2] is button.track_data:
			audio.stop_ambience()
		self.entries.remove(button)
		self.tracks.remove(button.track_data)
		app.destroy_object_tooltip(button)
		self.reindex_tracks()

	def blank_right_click_menu(self, event, blank):
		context_menu = tkinter.Menu(app, tearoff=0)

		context_menu.add_command(label="Remove Blank Space", command=lambda b=blank: self.remove_blank_space(b))
		try:
			context_menu.post(event.x_root, event.y_root)
		finally:
			context_menu.grab_release()

	def remove_blank_space(self, blank):
		self.entries.remove(blank)
		self.tracks.remove(blank.track_data)
		app.destroy_object_tooltip(blank)
		self.reindex_tracks()

	def column_label_right_click_menu(self, event):
		context_menu = tkinter.Menu(app, tearoff=0)

		enable_color_reset = False
		enable_volume_reset = False
		contains_non_ambient = False
		contains_non_loop = False
		for t in self.tracks:
			if "ambience" not in t or not t["ambience"]:
				contains_non_ambient = True
			if ("loop" in t and not t["loop"]) or ("loop" not in t and not data["loop"]):
				contains_non_loop = True
			if "color" in t:
				enable_color_reset = True
			if "volume" in t and t["volume"] != 1.0:
				enable_volume_reset = True

		context_menu.add_command(label="Change Column Label", command=self.change_column_label)
		context_menu.add_command(label="Overwrite Column Volume Settings", state="normal" if self.tracks else "disabled", command=self.change_column_volume)
		context_menu.add_command(label="Overwrite Column Colors", state="normal" if self.tracks else "disabled", command=self.change_column_colors)
		if contains_non_loop or not self.tracks:
			context_menu.add_command(label="Mark Column as Loopable", state="normal" if self.tracks else "disabled", command=self.mark_column_loop)
		else:
			context_menu.add_command(label="Mark Column as Non-Loopable", state="normal" if self.tracks else "disabled", command=self.mark_column_non_loop)
		if contains_non_ambient or not self.tracks:
			context_menu.add_command(label="Mark Column as Ambience", state="normal" if self.tracks else "disabled", command=self.mark_column_ambient)
		else:
			context_menu.add_command(label="Mark Column as Music", state="normal" if self.tracks else "disabled", command=self.mark_column_non_ambient)
		context_menu.add_separator()
		context_menu.add_command(label="Move Left", state="normal" if self.master.columns[0] is not self else "disabled", command=self.move_column_left)
		context_menu.add_command(label="Move Right", state="normal" if self.master.columns[-1] is not self else "disabled", command=self.move_column_right)
		context_menu.add_separator()
		context_menu.add_command(label="Reset Column Volume Settings", state="normal" if enable_volume_reset else "disabled", command=self.reset_column_volume)
		context_menu.add_command(label="Reset Column Colors", state="normal" if enable_color_reset else "disabled", command=self.reset_column_colors)
		context_menu.add_command(label="Remove Column", command=self.remove_column)
		try:
			context_menu.post(event.x_root, event.y_root)
		finally:
			context_menu.grab_release()

	def change_column_label(self):
		label = simpledialog.askstring(
			title="Change Column Label",
			prompt="Write new label:"
		)
		if not label:
			return
		self.title.configure(text=format_text(label))
		self.column_data["columnLabel"] = label
		app.data_changed()

	def change_column_volume(self):
		initial_vol = 1.0
		if audio.playing_data is not None and audio.playing_data[1] is self.column_data:
			if "volume" in audio.playing_data[2]:
				initial_vol = audio.playing_data[2]["volume"]
		elif audio.ambience_data is not None and audio.ambience_data[1] is self.column_data:
			if "volume" in audio.ambience_data[2]:
				initial_vol = audio.ambience_data[2]["volume"]
		else:
			for t in self.tracks:
				if "file" in t:
					if "volume" in t:
						initial_vol = t["volume"]
					break
		audio.temp_volume_cache = [1, self.column_data, initial_vol]
		VolumePopup(app, self.receive_column_volume, initial_vol)

	def receive_column_volume(self, value):
		for t in self.tracks:
			if "file" not in t:
				continue
			t["volume"] = value
		if audio.playing_data is not None and audio.playing_data[1] is self.column_data:
			audio.set_volume(value)
		if audio.ambience_data is not None and audio.ambience_data[1] is self.column_data:
			audio.set_volume(value, sfx=True)
		app.data_changed()

	def change_column_colors(self):
		color = colorchooser.askcolor()[1]
		if color is not None:
			for button in self.entries:
				if not isinstance(button, customtkinter.CTkButton):
					continue
				button.configure(fg_color=color, hover_color=hover_color(color), text_color=text_color(color))
				button.track_data["color"] = color
			app.data_changed()

	def mark_column_loop(self):
		for button in self.entries:
			if not isinstance(button, customtkinter.CTkButton):
				continue
			button.loop_var.set(True)
			if data["loop"]:
				button.track_data.pop("loop", None)
			else:
				button.track_data["loop"] = True
		app.data_changed()

	def mark_column_non_loop(self):
		for button in self.entries:
			if not isinstance(button, customtkinter.CTkButton):
				continue
			button.loop_var.set(False)
			if data["loop"]:
				button.track_data["loop"] = False
			else:
				button.track_data.pop("loop", None)
		app.data_changed()

	def mark_column_ambient(self):
		u = app.uses_ambience()
		if audio.playing_data is not None and audio.playing_data[1] is self.column_data:
			audio.stop_music()
		for button in self.entries:
			if not isinstance(button, customtkinter.CTkButton):
				continue
			button.ambience_var.set(True)
			button.track_data["ambience"] = True
		app.data_changed()
		if u != app.uses_ambience():
			app.load_header()

	def mark_column_non_ambient(self):
		u = app.uses_ambience()
		if audio.ambience_data is not None and audio.ambience_data[1] is self.column_data:
			audio.stop_ambience()
		for button in self.entries:
			if not isinstance(button, customtkinter.CTkButton):
				continue
			button.ambience_var.set(False)
			button.track_data.pop("ambience", None)
		app.data_changed()
		if u != app.uses_ambience():
			app.load_header()

	def move_column_left(self):
		index = self.master.columns.index(self)
		self.master.columns.insert(index - 1, self.master.columns.pop(index))
		app.page_view.reindex_columns()

	def move_column_right(self):
		index = self.master.columns.index(self)
		self.master.columns.insert(index + 1, self.master.columns.pop(index))
		app.page_view.reindex_columns()

	def reset_column_volume(self):
		if audio.playing_data is not None and audio.playing_data[1] is self.column_data:
			audio.set_volume(1)
		if audio.ambience_data is not None and audio.ambience_data[1] is self.column_data:
			audio.set_volume(1, sfx=True)
		for t in self.tracks:
			t.pop("volume", None)
		app.data_changed()

	def reset_column_colors(self):
		for button in self.entries:
			if not isinstance(button, customtkinter.CTkButton):
				continue
			button.configure(fg_color=data["color"], hover_color=hover_color(data["color"]), text_color=text_color(data["color"]))
			button.track_data.pop("color", None)
		app.data_changed()

	def remove_column(self):
		if audio.playing_data is not None and audio.playing_data[1] is self.column_data:
			audio.stop_music()
		if audio.ambience_data is not None and audio.ambience_data[1] is self.column_data:
			audio.stop_ambience()
		for e in self.entries:
			app.destroy_object_tooltip(e)
		app.page_view.columns.remove(self)
		app.page_view.page_data["columns"].remove(self.column_data)
		app.page_view.reindex_columns()
		self.destroy()



class AlternateTrackFrame(customtkinter.CTkFrame):
	def __init__(self, master, track_data, channel_dict):
		super().__init__(master)
		self.track_data = track_data
		self.channel_dict = channel_dict

		self.buttons = []

		for track in self.track_data["subdata"]:
			file = track["file"] if "file" in track else self.track_data["file"]
			button = customtkinter.CTkButton(self,
				text=format_text(track["sublabel"]),
				fg_color=DEFAULT_COLOR if "file" in track else ACCENT_COLOR,
				hover_color=DEFAULT_COLOR_HOVER if "file" in track else ACCENT_COLOR_HOVER,
				border_color="#FFFFFF",
				border_width=0,
				text_color_disabled="#D4D4D4",
				command=lambda f=self.channel_dict[file], t=track: audio.set_active_channel(f, t))
			button.grid(row=0, column=len(self.buttons), padx=(16, 4), pady=16, sticky="nsew")
			button.bind("<Button-2>", lambda event, b=button: self.atf_button_right_click_menu(event, b))
			button.bind("<Button-3>", lambda event, b=button: self.atf_button_right_click_menu(event, b))
			button.file = file
			button.subdata_entry = track
			self.buttons.append(button)

		self.grid_columnconfigure(tuple(range(len(self.buttons))), uniform="atf_buttons")

	def atf_button_right_click_menu(self, event, button):
		context_menu = tkinter.Menu(app, tearoff=0)
		context_menu.add_command(label="Change Label", command=lambda b=button: self.change_sublabel(b))
		context_menu.add_command(label="Move Left", state="normal" if self.buttons[0] is not button else "disabled", command=lambda b=button: self.move_atf_button_left(b))
		context_menu.add_command(label="Move Right", state="normal" if self.buttons[-1] is not button else "disabled", command=lambda b=button: self.move_atf_button_right(b))
		context_menu.add_separator()
		context_menu.add_command(label="Reset Label", command=lambda b=button: self.reset_sublabel(b))
		context_menu.add_command(label="Set as Default", state="normal" if "file" in button.subdata_entry else "disabled", command=lambda b=button: self.set_as_default(b))
		context_menu.add_command(label="Remove Linked Track", state="normal" if "file" in button.subdata_entry else "disabled", command=lambda b=button: self.remove_linked_track(b))
		try:
			context_menu.post(event.x_root, event.y_root)
		finally:
			context_menu.grab_release()

	def change_sublabel(self, button):
		label = simpledialog.askstring(
			title="Change Label",
			prompt="Write new label:"
		)
		if not label:
			return
		if button.winfo_exists():
			button.configure(text=format_text(label))
		button.subdata_entry["sublabel"] = label
		app.data_changed()

	def move_atf_button_left(self, button):
		index = self.buttons.index(button)
		self.buttons.insert(index - 1, self.buttons.pop(index))
		self.reindex_atf_buttons()

	def move_atf_button_right(self, button):
		index = self.buttons.index(button)
		self.buttons.insert(index + 1, self.buttons.pop(index))
		self.reindex_atf_buttons()

	def reset_sublabel(self, button):
		label = Path(button.file).stem
		if button.winfo_exists():
			button.configure(text=label)
		button.subdata_entry["sublabel"] = label
		app.data_changed()

	def set_as_default(self, button):
		for track in self.track_data["subdata"]:
			if "file" not in track:
				track["file"] = self.track_data["file"]
				self.track_data["file"] = button.subdata_entry["file"]
				button.subdata_entry.pop("file", None)
				app.data_changed()
				if "label" not in track:
					app.load_page(app.page_view.page_data)
				app.load_atf(self.track_data, self.channel_dict)
				return

	def remove_linked_track(self, button):
		self.track_data["subdata"].remove(button.subdata_entry)
		if len(self.track_data["subdata"]) > 1:
			self.buttons.remove(button)
			if button.winfo_exists():
				app.destroy_object_tooltip(button)
			self.reindex_atf_buttons()
		else:
			self.track_data.pop("subdata", None)
			app.data_changed()
			if app.alternate_track_frame is not None:
				app.after_idle(lambda a=app.alternate_track_frame: app.destroy_atf(a))

	def reindex_atf_buttons(self):
		for i, button in enumerate(self.buttons):
			button.subdata_entry["subindex"] = i
			if button.winfo_exists():
				button.grid(column=i)
		self.track_data["subdata"].sort(key=lambda x: x["subindex"])
		app.data_changed()



class LoadingPopup(customtkinter.CTkToplevel):
	def __init__(self, parent):
		super().__init__(parent)

		self.geometry("300x100")
		self.title("Downloading YouTube Video")
		self.attributes("-topmost", True)
		self.overrideredirect(True)
		self.grab_set()

		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		self.label = customtkinter.CTkLabel(self, text="Downloading...")
		self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")



class VolumePopup(customtkinter.CTkToplevel):
	def __init__(self, parent, callback, initial_vol, callback_param=None, global_volume_modifier=None):
		super().__init__(parent)
		self.callback = callback
		self.initial_vol = initial_vol
		self.callback_param = callback_param
		self.global_volume_modifier = global_volume_modifier

		self.title("Change Volume")
		self.attributes("-topmost", True)
		self.grab_set()

		self.grid_columnconfigure((0, 1), weight=1)

		self.frame = customtkinter.CTkFrame(self)
		self.frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
		self.frame.grid_columnconfigure(0, weight=1)
		self.frame.volume_info = customtkinter.CTkLabel(self.frame, text="")
		self.frame.volume_info.grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
		self.frame.volume_slider = customtkinter.CTkSlider(self.frame, from_=0, to=2 if self.global_volume_modifier is None else 1, command=self.set_volume_info)
		self.frame.volume_slider.set(self.initial_vol)
		self.set_volume_info(self.initial_vol)
		self.frame.volume_slider.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

		self.submit_button = customtkinter.CTkButton(self, text="OK", command=self.submit)
		self.submit_button.grid(row=1, column=0, padx=10, pady=10)
		self.cancel_button = customtkinter.CTkButton(self, text="Cancel", command=self.cancel)
		self.cancel_button.grid(row=1, column=1, padx=10, pady=10)
		self.bind("<Return>", self.submit)
		self.bind("<Escape>", self.cancel)

	def set_volume_info(self, value):
		self.frame.volume_info.configure(text=f"New volume: {value:.0%}")
		if self.global_volume_modifier is None:
			if audio.temp_volume_cache is not None or self.global_volume_modifier is not None:
				audio.temp_volume_cache[2] = value
				if audio.playing_data is not None and audio.playing_data[audio.temp_volume_cache[0]] is audio.temp_volume_cache[1]:
					audio.set_volume(value, save=False)
				if audio.ambience_data is not None and audio.ambience_data[audio.temp_volume_cache[0]] is audio.temp_volume_cache[1]:
					audio.set_volume(value, sfx=True, save=False)
		else:
			if self.global_volume_modifier == "bgm":
				if audio.playing_data is not None:
					audio.set_volume(audio.playing_data[2]["volume"] if "volume" in audio.playing_data[2] else 1, save=False, temp_global_volume=value)
			else:
				if audio.ambience_data is not None:
					audio.set_volume(audio.ambience_data[2]["volume"] if "volume" in audio.ambience_data[2] else 1, sfx=True, save=False, temp_global_volume=value)

	def submit(self, event=None):
		audio.temp_volume_cache = None
		if self.callback_param is None:
			self.callback(self.frame.volume_slider.get())
		else:
			self.callback(self.frame.volume_slider.get(), self.callback_param)
		self.destroy()

	def cancel(self, event=None):
		if self.global_volume_modifier is None:
			if audio.temp_volume_cache is not None:
				if audio.playing_data is not None and audio.playing_data[audio.temp_volume_cache[0]] is audio.temp_volume_cache[1]:
					audio.set_volume(audio.main_backup_vol, save=False, absolute=True)
				if audio.ambience_data is not None and audio.ambience_data[audio.temp_volume_cache[0]] is audio.temp_volume_cache[1]:
					audio.set_volume(audio.ambience_backup_vol, sfx=True, save=False, absolute=True)
		else:
			if self.global_volume_modifier == "bgm":
				audio.set_volume(audio.main_backup_vol, save=False, absolute=True)
			else:
				audio.set_volume(audio.ambience_backup_vol, sfx=True, save=False, absolute=True)
		audio.temp_volume_cache = None
		self.destroy()



class TextVolumePopup(customtkinter.CTkToplevel):
	def __init__(self, parent, callback, button, column, initial_vol):
		super().__init__(parent)
		self.callback = callback
		self.button = button
		self.column = column
		self.initial_vol = initial_vol
		self.used_sample_play = False

		self.title("Change Label/Volume")
		self.attributes("-topmost", True)
		self.grab_set()

		self.grid_columnconfigure((0, 1), weight=1)

		self.label_frame = customtkinter.CTkFrame(self)
		self.label_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
		self.label_frame.grid_columnconfigure(0, weight=1)
		self.label_frame.label_info = customtkinter.CTkLabel(self.label_frame, text="New label:")
		self.label_frame.label_info.grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
		self.label_frame.label_entry = customtkinter.CTkEntry(self.label_frame)
		self.label_frame.label_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

		self.volume_frame = customtkinter.CTkFrame(self)
		self.volume_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
		self.volume_frame.grid_columnconfigure((0, 1), weight=1)
		self.volume_frame.volume_info = customtkinter.CTkLabel(self.volume_frame, text="")
		self.volume_frame.volume_info.grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
		self.volume_frame.play_button = customtkinter.CTkButton(self.volume_frame, text="Play", command=self.sample_play)
		self.volume_frame.play_button.grid(row=0, column=1, padx=10, pady=(10,0), sticky="e")
		self.volume_frame.volume_slider = customtkinter.CTkSlider(self.volume_frame, from_=0, to=2, command=self.set_volume_info)
		self.volume_frame.volume_slider.set(self.initial_vol)
		self.set_volume_info(self.initial_vol)
		self.volume_frame.volume_slider.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

		self.submit_button = customtkinter.CTkButton(self, text="OK", command=self.submit)
		self.submit_button.grid(row=2, column=0, padx=10, pady=10)
		self.cancel_button = customtkinter.CTkButton(self, text="Cancel", command=self.cancel)
		self.cancel_button.grid(row=2, column=1, padx=10, pady=10)
		self.bind("<Return>", self.submit)
		self.bind("<Escape>", self.cancel)

	def sample_play(self):
		self.used_sample_play = True
		threading.Thread(target=self.column.play_audio_button, args=(self.column.master.page_data, self.column.column_data, self.button.track_data), daemon=True).start()

	def set_volume_info(self, value):
		self.volume_frame.volume_info.configure(text=f"New volume: {value:.0%}")
		audio.temp_volume_cache[2] = value
		if audio.playing_data is not None and audio.playing_data[2] is self.button.track_data:
			audio.set_volume(value, save=False)
		if audio.ambience_data is not None and audio.ambience_data[2] is self.button.track_data:
			audio.set_volume(value, sfx=True, save=False)

	def submit(self, event=None):
		audio.temp_volume_cache = None
		if self.used_sample_play:
			ambience = self.button.track_data["ambience"] if "ambience" in self.button.track_data else False
			if not ambience:
				audio.stop_music(force_instant=True)
			else:
				audio.stop_ambience(force_instant=True)
		self.callback(self.button, self.label_frame.label_entry.get(), self.volume_frame.volume_slider.get())
		self.destroy()

	def cancel(self, event=None):
		if self.used_sample_play:
			ambience = self.button.track_data["ambience"] if "ambience" in self.button.track_data else False
			if not ambience:
				audio.stop_music(force_instant=True)
			else:
				audio.stop_ambience(force_instant=True)
		else:
			if audio.playing_data is not None and audio.playing_data[2] is self.button.track_data:
				audio.set_volume(audio.main_backup_vol, save=False, absolute=True)
			if audio.ambience_data is not None and audio.ambience_data[2] is self.button.track_data:
				audio.set_volume(audio.ambience_backup_vol, sfx=True, save=False, absolute=True)
		audio.temp_volume_cache = None
		self.destroy()



root = customtkinter.CTk()
root.withdraw()

highlight_font = customtkinter.CTkFont(weight="bold")
normal_font = customtkinter.CTkFont(weight="normal")
show_track_count = customtkinter.BooleanVar(value=False)
bird = customtkinter.BooleanVar(value=True)

initialize_data()
initialize_app()

playlist_mode = customtkinter.BooleanVar(value=False)
autosave = customtkinter.BooleanVar(value=settings["autosave"])
enable_tooltips = customtkinter.BooleanVar(value=settings["tooltips"])
audio_device_var = customtkinter.StringVar(value=settings["audioDevice"] if "audioDevice" in settings else "DEFAULT")

finalize_app()

root.mainloop()