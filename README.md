# Music Playlist Manager

A Flask + SQLite web app to manage a music library and custom playlists.

## Features
- Browse and search songs by title, artist, or genre
- Add and delete songs
- Create playlists
- Add songs to playlists and remove them
- Persistent SQLite database
- Responsive dark music-inspired UI

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   python app.py
   ```
5. Visit http://127.0.0.1:5000

The SQLite database (`music_manager.db`) is created automatically on first run.

## Deploy to Render
This project includes `render.yaml` and `Procfile`. Push the files to a Git repository and create a new Render web service from that repository. For persistent production data, attach a persistent disk and set `DATABASE_PATH` to a path on that disk.
