# Audion – Ultimate Playlist Analyzer
import os
import re
import sys
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
# ----------------------- THEME / CONSTANTS (must be defined before window) -----------------------
BG_MAIN = "#0F172A"
BG_PANEL = "#020617"
BG_CARD = "#0b1220"
BG_CARD2 = "#0f172a"
ACCENT = "#6366F1"
ACCENT_SOFT = "#22C55E"
FG_TEXT = "#E5E7EB"
FG_MUTED = "#9CA3AF"
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUB = ("Segoe UI", 14, "bold")
FONT_TEXT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
plt.rcParams.update({
    'text.color': FG_TEXT,
    'axes.labelcolor': FG_TEXT,
    'axes.titlecolor': FG_TEXT,
    'xtick.color': FG_TEXT,
    'ytick.color': FG_TEXT,
    'figure.facecolor': BG_MAIN,
    'axes.facecolor': BG_MAIN,
    'axes.edgecolor': '#334155'
})
# ----------------------- Mood detection maps -----------------------
MOOD_KEYWORDS = {
    "Happy": ["happy", "joy", "sun", "sunshine", "smile", "bright", "good", "fun", "dance", "party", "better", "alive", "smiling", "golden"],
    "Sad": ["sad", "lonely", "cry", "tears", "heartbreak", "broken", "miss", "lost", "blue", "alone"],
    "Energetic": ["fire", "power", "wild", "run", "loud", "fast", "hype", "energy", "rock", "boom", "beat", "crazy"],
    "Calm": ["calm", "soft", "slow", "chill", "lofi", "peace", "relax", "quiet", "soothing", "sleep"],
    "Romantic": ["love", "lover", "heart", "kiss", "romantic", "baby", "sweet", "darling", "mine", "forever"]
}
GENRE_MOOD = {
    "lofi": "Calm", "lo-fi": "Calm", "lo fi": "Calm", "indie": "Calm",
    "romantic": "Romantic", "pop": "Happy", "sad": "Sad", "classical": "Calm",
    "edm": "Energetic", "dance": "Energetic", "rock": "Energetic",
    "r&b": "Romantic", "soul": "Romantic"
}
YEAR_RE = re.compile(r"(19|20)\d{2}")
# ----------------------- Data loading (safe fallback) -----------------------
def safe_load_excel(path="Copy of audion.xlsx"):
    try:
        df_local = pd.read_excel(path)
        df_local = df_local.dropna(how="all")
        if "Name" not in df_local.columns:
            raise ValueError("Excel missing required 'Name' column.")
        return df_local
    except Exception as e:
        # Fallback sample dataset to keep the program runnable
        sample = [
            {"Name": "Unstoppable", "Artist": "Sia", "Genre": "Pop", "Language": "English", "Duration": "03:02"},
            {"Name": "Faded", "Artist": "Alan Walker", "Genre": "EDM", "Language": "English", "Duration": "03:32"},
            {"Name": "LoFi Nights", "Artist": "Indie Cafe with a very very long name that was cutting off", "Genre": "Lofi", "Language": "Instrumental", "Duration": "02:45"},
            {"Name": "Melancholy Ballad", "Artist": "Heartstring", "Genre": "Ballad", "Language": "English", "Duration": "04:10"},
            {"Name": "Dancefloor Dream", "Artist": "Neon Beats", "Genre": "Dance", "Language": "English", "Duration": "03:21"},
        ]
        return pd.DataFrame(sample)
df = safe_load_excel("Copy of audion.xlsx")
# Normalize basic columns
df = df.fillna("")
if "index" in df.columns:
    try:
        df.set_index("index", inplace=True)
    except Exception:
        pass
df["Language"] = df.get("Language", "").astype(str).fillna("Unknown").str.strip()
df["Genre"] = df.get("Genre", "").astype(str).fillna("Unknown").str.strip()
df["Duration"] = df.get("Duration", "").astype(str).fillna("").str.strip()
def parse_duration(duration_str):
    """''''''Convert 'mm:ss' or 'hh:mm:ss' to minutes (float).''''''"""
    if pd.isna(duration_str) or not str(duration_str).strip():
        return 0.0
    s = str(duration_str).strip()
    parts = s.split(":")
    try:
        parts = [int(p) for p in parts]
    except:
        nums = re.findall(r"\d+", s)
        if len(nums) >= 2:
            parts = [int(n) for n in nums[-2:]]
        else:
            return 0.0
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes + seconds / 60.0
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 60 + minutes + seconds / 60.0
    else:
        return 0.0
df["Duration_min"] = df["Duration"].apply(parse_duration)
def detect_mood(title, genre):
    title = str(title or "").lower()
    genre = str(genre or "").lower()
    for g in GENRE_MOOD:
        if g in genre:
            return GENRE_MOOD[g]
    for mood, words in MOOD_KEYWORDS.items():
        for w in words:
            if w in title:
                return mood
    return "Unknown"
def infer_mood_fallback(genre):
    genre_lower = str(genre).lower()
    MOOD_MAP = {
        "pop": "Happy", "dance": "Party", "edm": "Energetic", "rock": "Intense",
        "indie": "Chill", "folk": "Calm", "ballad": "Romantic", "romantic": "Romantic",
        "hip hop": "Confident", "r&b": "Smooth", "k-pop": "Energetic", "bollywood": "Romantic"
    }
    for key, mood in MOOD_MAP.items():
        if key in genre_lower:
            return mood
    return "Mixed"
def detect_or_infer_mood(row):
    mood = detect_mood(row.get("Name", ""), row.get("Genre", ""))
    if mood == "Unknown":
        return infer_mood_fallback(row.get("Genre", ""))
    return mood

df["Mood"] = df.apply(detect_or_infer_mood, axis=1)
# Simulate simple audio features so charts look interesting
def simulate_audio_features(row):
    genre = str(row["Genre"]).lower()
    duration = row["Duration_min"]
    energy = 0.7 if ("edm" in genre or "dance" in genre) else 0.5
    danceability = 0.8 if ("pop" in genre or "dance" in genre) else 0.4
    valence = 0.6 if ("happy" in str(row["Mood"]).lower() or "party" in str(row["Mood"]).lower()) else 0.4
    tempo = max(60, int(np.random.normal(128 if energy > 0.6 else 100, 15)))
    return pd.Series({"energy": energy, "danceability": danceability, "valence": valence, "tempo": tempo})

audio_features = df.apply(simulate_audio_features, axis=1)
df = pd.concat([df, audio_features], axis=1)
# ----------------------- GLOBALS & STATE -----------------------
selected_songs = {}      # playlist (by dataframe index)
current_filtered_df = df.copy()
card_total = card_selected = card_duration = card_moods = card_languages = None
card_pl_total_duration = card_pl_avg_length = card_pl_top_artist = card_pl_top_genre = None
queue = []               # list of df indices in play order
current_track_idx = None
is_playing = False
play_position_seconds = 0
progress_update_job = None
# ----------------------- MAIN WINDOW -----------------------
window = tk.Tk()
window.title("🎵 Audion – Ultimate Playlist Analyzer")
window.geometry("1280x780")
window.configure(bg=BG_MAIN)
window.minsize(1000, 650)
style = ttk.Style(window)
try:
    style.theme_use("clam")
except:
    pass
style.configure("Treeview", background=BG_CARD, foreground=FG_TEXT, fieldbackground=BG_CARD, rowheight=28)
style.configure("Treeview.Heading", background=BG_PANEL, foreground=FG_TEXT, font=("Segoe UI", 10, "bold"))
style.map("Accent.TButton", background=[("active", "#4F46E5")])
# Header
header_frame = tk.Frame(window, bg=BG_PANEL, height=60)
header_frame.pack(side="top", fill="x")
ttk.Label(header_frame, text="🎵 Audion", font=("Segoe UI", 16, "bold"), foreground=FG_TEXT, background=BG_PANEL).pack(side="left", padx=18, pady=12)
ttk.Label(header_frame, text="Ultimate Playlist Analyzer", font=("Segoe UI", 10), foreground=FG_MUTED, background=BG_PANEL).pack(side="left", padx=6, pady=18)
# Layout frames
main_frame = tk.Frame(window, bg=BG_MAIN)
main_frame.pack(fill="both", expand=True, padx=8, pady=(8, 8))   # reduced outer padding so left area can expand
left_frame = tk.Frame(main_frame, bg=BG_MAIN)
left_frame.pack(side="left", fill="both", expand=True)
right_frame = tk.Frame(main_frame, bg=BG_MAIN, width=360)
right_frame.pack(side="right", fill="y", padx=(8, 4))  # reduced left padding so table has more room
# Search bar
search_bar = tk.Frame(left_frame, bg=BG_MAIN)
search_bar.pack(fill="x", pady=(0, 8))
search_var = tk.StringVar()
search_entry = tk.Entry(search_bar, textvariable=search_var, font=FONT_TEXT, bg="white", fg="black", insertbackground=FG_TEXT, relief="flat")
search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=6)
languages = sorted(df["Language"].unique())
selected_language = tk.StringVar(value="All")
language_combo = ttk.Combobox(search_bar, textvariable=selected_language, values=["All"] + languages, state="readonly", width=12)
language_combo.pack(side="right", padx=(8, 0))
genres = ["All"] + sorted(df["Genre"].unique())
selected_genre = tk.StringVar(value="All")
genre_combo = ttk.Combobox(search_bar, textvariable=selected_genre, values=genres, state="readonly", width=14)
genre_combo.pack(side="right")
# Song table
table_frame = tk.Frame(left_frame, bg=BG_MAIN)
table_frame.pack(fill="both", expand=True)
columns = ("Artist", "Genre", "Duration")
tree = ttk.Treeview(table_frame, columns=columns, show="headings")
tree.heading("Artist", text="Artist/Title")
tree.heading("Genre", text="Genre")
tree.heading("Duration", text="Duration")
# increased artist width and allow stretching; display both title and artist in one column
tree.column("Artist", width=700, minwidth=300, anchor="w")
tree.column("Genre", width=140, minwidth=80, anchor="w")
tree.column("Duration", width=80, minwidth=60, anchor="center")
tree.grid(row=0, column=0, sticky="nsew")
# Vertical + Horizontal scrollbars for full visibility of long artist strings
table_scroll_v = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
table_scroll_h = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=table_scroll_v.set, xscrollcommand=table_scroll_h.set)
table_scroll_v.grid(row=0, column=1, sticky="ns")
table_scroll_h.grid(row=1, column=0, sticky="ew")
table_frame.grid_rowconfigure(0, weight=1)
table_frame.grid_columnconfigure(0, weight=1)
# Right sidebar stats
stats_panel = tk.Frame(right_frame, bg=BG_MAIN)
stats_panel.pack(fill="both", expand=True)
tk.Label(stats_panel, text="📊 Live Stats", bg=BG_MAIN, fg=ACCENT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(6, 6))
def create_stat_line(parent, label_text):
    f = tk.Frame(parent, bg=BG_CARD, relief="flat", bd=0)
    f.pack(fill="x", padx=8, pady=6)
    tk.Label(f, text=label_text, bg=BG_CARD, fg=FG_MUTED, font=FONT_SMALL).pack(side="left", padx=(8,0), pady=8)
    val = tk.Label(f, text="", bg=BG_CARD, fg=FG_TEXT, font=FONT_TEXT)
    val.pack(side="right", padx=8)
    return val
card_total = create_stat_line(stats_panel, "Library Songs")
card_selected = create_stat_line(stats_panel, "Playlist Songs")
card_duration = create_stat_line(stats_panel, "Avg Duration")
card_moods = create_stat_line(stats_panel, "Mood Diversity")
card_languages = create_stat_line(stats_panel, "Languages")
card_pl_total_duration = create_stat_line(stats_panel, "Playlist Total")
card_pl_avg_length = create_stat_line(stats_panel, "Playlist Avg")
card_pl_top_artist = create_stat_line(stats_panel, "Top Artist")
card_pl_top_genre = create_stat_line(stats_panel, "Top Genre")
# Controls
controls_frame = tk.Frame(right_frame, bg=BG_MAIN)
controls_frame.pack(fill="x", padx=8, pady=(6, 10))
ttk.Button(controls_frame, text="💾 Export CSV", command=lambda: export_playlist_csv()).pack(side="left", padx=6)
ttk.Button(controls_frame, text="📝 Export Summary", command=lambda: export_playlist_summary_txt()).pack(side="left", padx=6)
ttk.Button(controls_frame, text="✨ Recommend", command=lambda: show_mood_recommendations()).pack(side="left", padx=6)
ttk.Button(controls_frame, text="🎨 Wrapped", command=lambda: open_ultimate_dashboard()).pack(side="left", padx=6)
queue_toggle = tk.BooleanVar(value=True)
tk.Checkbutton(controls_frame, text="Show Queue", variable=queue_toggle, bg=BG_MAIN, fg=FG_TEXT, selectcolor=BG_PANEL).pack(side="right")
queue_frame = tk.Frame(right_frame, bg=BG_MAIN)
queue_frame.pack(fill="both", expand=False, padx=8, pady=(8, 0))
queue_listbox = tk.Listbox(queue_frame, bg=BG_CARD, fg=FG_TEXT, height=6, activestyle="none", selectbackground=ACCENT)
queue_listbox.pack(fill="both", expand=True, pady=(6,0))
# ----------------------- CORE FUNCTIONS -----------------------
def format_minutes(mins_float):
    if mins_float is None or (isinstance(mins_float, float) and np.isnan(mins_float)):
        return "0:00"
    total_seconds = int(round(mins_float * 60))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"
def compute_playlist_summary(pl_df):
    if pl_df.empty:
        return {"total_min": 0.0, "avg_min": 0.0, "top_artist": "N/A", "top_genre": "N/A", "top_language": "N/A"}
    total_min = pl_df["Duration_min"].sum()
    avg_min = pl_df["Duration_min"].mean()
    top_artist = pl_df["Artist"].value_counts().idxmax() if "Artist" in pl_df.columns and not pl_df["Artist"].isna().all() else "Unknown"
    top_genre = pl_df["Genre"].value_counts().idxmax() if "Genre" in pl_df.columns and not pl_df["Genre"].isna().all() else "Unknown"
    top_language = pl_df["Language"].value_counts().idxmax() if "Language" in pl_df.columns and not pl_df["Language"].isna().all() else "Unknown"
    return {"total_min": total_min, "avg_min": avg_min, "top_artist": top_artist, "top_genre": top_genre, "top_language": top_language}
def generate_text_insight(pl_df, summary):
    if pl_df.empty:
        return "No songs selected. Add some tracks to see a playlist summary and insights."
    lines = []
    lines.append(f"Total duration: {format_minutes(summary['total_min'])} • Avg length: {format_minutes(summary['avg_min'])}")
    lines.append(f"Top artist: {summary['top_artist']} • Top genre: {summary['top_genre']} • Top language: {summary.get('top_language', 'N/A')}")
    dominant_mood = pl_df["Mood"].value_counts().idxmax() if "Mood" in pl_df.columns and not pl_df["Mood"].isna().all() else None
    if dominant_mood:
        lines.append(f"Dominant mood: {dominant_mood}. Try adding a contrasting track to vary the vibe.")
    else:
        lines.append("Mood info unavailable.")
    return "\n".join(lines)
def get_playlist_df():
    if not selected_songs:
        return pd.DataFrame(columns=df.columns)
    indices = list(selected_songs.keys())
    # Some indices might not exist in df if df was reloaded; filter
    indices = [i for i in indices if i in df.index]
    pl_df = df.loc[indices].copy()
    pl_df.reset_index(drop=True, inplace=True)
    return pl_df
def export_playlist_csv():
    pl_df = get_playlist_df()
    if pl_df.empty:
        messagebox.showwarning("No data", "No playlist to export.")
        return
    pl_df.to_csv("audion_playlist.csv", index=False)
    messagebox.showinfo("Exported", "Saved as audion_playlist.csv")
def export_playlist_summary_txt():
    pl_df = get_playlist_df()
    summary = compute_playlist_summary(pl_df)
    if pl_df.empty:
        messagebox.showwarning("No data", "No playlist to export.")
        return
    text = []
    text.append(f"Playlist Summary - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    text.append(f"Tracks: {len(pl_df)}")
    text.append(f"Total duration: {format_minutes(summary['total_min'])}")
    text.append(f"Average track length: {format_minutes(summary['avg_min'])}")
    text.append(f"Top artist: {summary['top_artist']}")
    text.append(f"Top genre: {summary['top_genre']}")
    text.append("")
    text.append("Track list:")
    for i, r in pl_df.iterrows():
        text.append(f"{i+1}. {r.get('Name','')} | {r.get('Artist','')} ({format_minutes(r.get('Duration_min',0.0))})")
    fname = "audion_playlist_summary.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(text))
    messagebox.showinfo("Exported", f"Saved summary as {fname}")
# Recommendation helpers
def generate_mood_recommendations(pl_df, n=8):
    if pl_df.empty:
        return pd.DataFrame()
    dominant = pl_df["Mood"].value_counts().idxmax()
    contrast_map = {
        "Happy": ["Sad", "Calm", "Romantic"],
        "Sad": ["Happy", "Energetic"],
        "Energetic": ["Calm", "Romantic"],
        "Calm": ["Energetic", "Happy"],
        "Romantic": ["Energetic", "Happy"],
        "Mixed": ["Calm", "Happy"]
    }
    candidates = contrast_map.get(dominant, ["Calm", "Happy"])
    available = df.drop(index=list(selected_songs.keys()), errors="ignore").copy()
    recs = available[available["Mood"].isin(candidates)]
    if recs.empty:
        recs = available.sample(min(n, len(available))) if len(available) > 0 else pd.DataFrame()
    else:
        recs = recs.sample(min(n, len(recs)))
    return recs
def show_mood_recommendations():
    pl_df = get_playlist_df()
    if pl_df.empty:
        messagebox.showwarning("No playlist", "Select songs first to get recommendations.")
        return
    recs = generate_mood_recommendations(pl_df, n=8)
    if recs.empty:
        messagebox.showinfo("Recommendations", "No recommendations available.")
        return
    top = tk.Toplevel(window)
    top.title("Recommendations | Mood Contrast")
    top.geometry("560x420")
    top.configure(bg=BG_MAIN)
    tk.Label(top, text="Try adding these to contrast the playlist mood:", bg=BG_PANEL, fg=FG_TEXT, font=("Segoe UI", 12, "bold")).pack(fill="x", padx=8, pady=8)
    listbox = tk.Listbox(top, bg=BG_CARD, fg=FG_TEXT)
    listbox.pack(fill="both", expand=True, padx=8, pady=8)
    recs = recs.reset_index()  # keep original df index in 'index' column
    for i, r in recs.iterrows():
        listbox.insert(tk.END, f"{r.get('Name','')} | {r.get('Artist','')} • {r.get('Mood','')}")
    def add_selected_recs():
        sel = listbox.curselection()
        for s in sel:
            idx = int(recs.loc[s, "index"])
            add_to_playlist(idx)
        top.destroy()
    tk.Button(top, text="Add selected", command=add_selected_recs, bg=BG_CARD, fg=FG_TEXT).pack(pady=8)
# ----------------------- TABLE & PLAYLIST UI functions -----------------------
def update_library_stats():
    avg_duration = df["Duration_min"].mean() if not df["Duration_min"].isna().all() else 0.0
    mins, secs = divmod(int(avg_duration * 60), 60)
    card_total.config(text=str(len(df)))
    card_duration.config(text=f"{mins}:{secs:02d}")
    card_languages.config(text=str(df["Language"].nunique()))
def apply_filters(event=None):
    global current_filtered_df
    lang = selected_language.get()
    genre = selected_genre.get()
    query = search_var.get().strip().lower()
    current_filtered_df = df.copy()
    if lang and lang != "All":
        current_filtered_df = current_filtered_df[current_filtered_df["Language"] == lang]
    if genre and genre != "All":
        current_filtered_df = current_filtered_df[current_filtered_df["Genre"] == genre]
    if query:
        mask = current_filtered_df["Name"].str.lower().str.contains(query, na=False) | current_filtered_df["Artist"].str.lower().str.contains(query, na=False)
        current_filtered_df = current_filtered_df[mask]
    populate_table()
    update_status_bar()
def populate_table():
    for i in tree.get_children():
        tree.delete(i)
    for idx, row in current_filtered_df.iterrows():
        display_title = row["Name"]
        display_artist = row.get("Artist", "")
        dur = format_minutes(row.get("Duration_min", 0.0))
        artist_cell = f"{display_title} | {display_artist}"
        tree.insert("", "end", iid=str(idx), values=(artist_cell, row.get("Genre", ""), dur))
    update_library_stats()
def update_status_bar():
    shown = len(current_filtered_df)
    selected = len(selected_songs)
    status_bar.config(text=f"Showing {shown} songs · {selected} selected")
def on_song_click(event):
    item = tree.focus()
    if not item:
        return
    try:
        add_to_playlist(int(item))
    except:
        pass
tree.bind("<Double-1>", on_song_click)
def add_to_playlist(index):
    index = int(index)
    if index not in df.index:
        return
    selected_songs[index] = df.loc[index].to_dict()
    if index not in queue:
        queue.append(index)
    update_playlist_widgets()
def remove_from_playlist(index):
    index = int(index)
    selected_songs.pop(index, None)
    try:
        queue.remove(index)
    except ValueError:
        pass
    update_playlist_widgets()
def update_playlist_widgets():
    card_selected.config(text=str(len(selected_songs)))
    pl_df = get_playlist_df()
    card_moods.config(text=str(pl_df["Mood"].nunique() if not pl_df.empty else 0))
    summary = compute_playlist_summary(pl_df)
    card_pl_total_duration.config(text=format_minutes(summary["total_min"]))
    card_pl_avg_length.config(text=format_minutes(summary["avg_min"]))
    card_pl_top_artist.config(text=summary["top_artist"])
    card_pl_top_genre.config(text=summary["top_genre"])
    queue_listbox.delete(0, tk.END)
    for i, idx in enumerate(queue):
        if idx in df.index:
            name = df.loc[idx, "Name"]
            artist = df.loc[idx, "Artist"] if "Artist" in df.columns else ""
            queue_listbox.insert(tk.END, f"{i+1}. {name} | {artist}")
    update_status_bar()
# Right-click menu
menu = tk.Menu(window, tearoff=0)
def on_add_selected():
    sel = tree.selection()
    for s in sel:
        add_to_playlist(int(s))
menu.add_command(label="Add to Playlist", command=on_add_selected)
def on_remove_selected():
    sel = tree.selection()
    for s in sel:
        remove_from_playlist(int(s))
menu.add_command(label="Remove from Playlist", command=on_remove_selected)
def on_show_menu(event):
    rowid = tree.identify_row(event.y)
    if rowid:
        tree.selection_set(rowid)
        menu.post(event.x_root, event.y_root)
tree.bind("<Button-3>", on_show_menu)  # right click
# ----------------------- Playback & progress -----------------------
bottom_action_frame = tk.Frame(bg=BG_MAIN)
bottom_action_frame.pack(fill="x", pady=(8, 6))
tk.Button(bottom_action_frame, text="➕ Add Selected to Playlist", bg=BG_CARD, fg=FG_TEXT, relief="flat",
          command=lambda: [add_to_playlist(int(s)) for s in tree.selection()]).pack(side="left", padx=6)
tk.Button(bottom_action_frame, text="➖ Remove Selected", bg=BG_CARD, fg=FG_TEXT, relief="flat",
          command=lambda: [remove_from_playlist(int(s)) for s in tree.selection()]).pack(side="left", padx=6)
# ----------------------- Dashboard charts helpers -----------------------
def create_donut_chart(parent, dfc, column, title, row, col, colors=None):
    # Slightly nudge the pie right so labels (if long) don't overlap
    fig = Figure(figsize=(4.2, 3.2), facecolor=BG_MAIN)
    ax = fig.add_subplot(111)
    counts = dfc[column].value_counts().head(6)
    if len(counts) > 0:
        wedges, texts, autotexts = ax.pie(counts.values, labels=counts.index, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4))
        # make sure labels don't overlap with left edge
        fig.subplots_adjust(left=0.18, right=0.98)
    ax.set_title(title, fontsize=10, pad=12)
    fig.patch.set_facecolor(BG_MAIN)
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
def create_horizontal_bar(parent, series, title, row, col, color=None):
    # make the figure wider and shift content to the right so y-labels (artists) are fully visible
    fig = Figure(figsize=(6.5, 2.6), facecolor=BG_MAIN)
    ax = fig.add_subplot(111)
    if not series.empty:
        y_pos = np.arange(len(series))
        ax.barh(y_pos, series.values)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(series.index, fontsize=8)
        ax.invert_yaxis()
        # increase left margin so long artist names fit | moves bars to the right
        fig.subplots_adjust(left=0.38, right=0.98, top=0.9, bottom=0.12)
    else:
        fig.subplots_adjust(left=0.12, right=0.98)
    ax.set_title(title, fontsize=10)
    fig.patch.set_facecolor(BG_MAIN)
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
def create_pie_chart(parent, series, title, row, col):
    fig = Figure(figsize=(4.2, 3.2), facecolor=BG_MAIN)
    ax = fig.add_subplot(111)
    if not series.empty:
        ax.pie(series.values, labels=series.index, autopct='%1.1f%%')
        fig.subplots_adjust(left=0.18, right=0.98)
    ax.set_title(title, fontsize=10)
    fig.patch.set_facecolor(BG_MAIN)
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
def create_histogram(parent, series, title, row, col, span=1):
    fig = Figure(figsize=(8.6, 3.2), facecolor=BG_MAIN)
    ax = fig.add_subplot(111)
    ax.hist(series.dropna(), bins=15)
    ax.set_title(title, fontsize=10)
    # nudge histogram right a little so axis labels are not clipped
    fig.subplots_adjust(left=0.12, right=0.98)
    fig.patch.set_facecolor(BG_MAIN)
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().grid(row=row, column=col, columnspan=span, padx=6, pady=6, sticky="nsew")
def open_ultimate_dashboard():
    pl_df = get_playlist_df()
    if pl_df.empty:
        messagebox.showwarning("No Playlist", "Select songs atleast one song!")
        return
    win = tk.Toplevel(window)
    win.title("🎨 Audion Wrapped – Ultimate Analysis")
    win.configure(bg=BG_MAIN)
    win.geometry('1400x2100')
    win.state("zoomed")
    header = tk.Frame(win, bg=BG_PANEL, height=90)
    header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 10))
    total_min = pl_df["Duration_min"].sum()
    primary_mood = pl_df["Mood"].value_counts().idxmax() if not pl_df.empty else "Mixed"
    tk.Label(header, text="🎵 Your Playlist Wrapped", bg=BG_PANEL, fg=FG_TEXT, font=("Segoe UI", 18, "bold")).pack(side="left", padx=18, pady=18)
    tk.Label(header, text=f"{len(pl_df)} songs • {format_minutes(total_min)} • {primary_mood} vibes", bg=BG_PANEL, fg=ACCENT, font=("Segoe UI", 10, "bold")).pack(side="right", padx=18, pady=18)
    notebook = ttk.Notebook(win)
    notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 12))
    overview_frame = tk.Frame(notebook, bg=BG_MAIN)
    notebook.add(overview_frame, text="📊 Overview")
    charts_layout = tk.Frame(overview_frame, bg=BG_MAIN)
    charts_layout.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
    for r in range(4):
        charts_layout.grid_rowconfigure(r, weight=1, pad=4)
    for c in range(2):
        charts_layout.grid_columnconfigure(c, weight=1, pad=4)
    create_donut_chart(charts_layout, pl_df, "Genre", "Genres", 0, 0)
    # pass top 8 artists to make space for names
    create_horizontal_bar(charts_layout, pl_df["Artist"].value_counts().head(8), "Top Artists", 0, 1)
    create_pie_chart(charts_layout, pl_df["Language"].value_counts().head(5), "Languages", 1, 0)
    create_donut_chart(charts_layout, pl_df, "Mood", "Mood Distribution", 1, 1)
    summary = compute_playlist_summary(pl_df)
    tk.Label(charts_layout, text=generate_text_insight(pl_df, summary), justify="left", bg=BG_CARD2, fg=FG_TEXT, wraplength=900).grid(row=2, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
    create_histogram(charts_layout, pl_df["Duration_min"], "Song Lengths (min)", 3, 0, span=2)
# ----------------------- Events, initialization -----------------------
search_var.trace_add("write", lambda *args: apply_filters())
language_combo.bind("<<ComboboxSelected>>", apply_filters)
genre_combo.bind("<<ComboboxSelected>>", apply_filters)
status_bar = tk.Label(window, text="Ready • 0 selected", bg=BG_PANEL, fg=FG_MUTED, font=FONT_SMALL, anchor="w")
status_bar.pack(side="bottom", fill="x")
apply_filters()
update_library_stats()
update_playlist_widgets()
window.mainloop()
