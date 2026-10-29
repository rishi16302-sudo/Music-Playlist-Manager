import os
from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-for-production")
init_db()

@app.context_processor
def inject_counts():
    with get_db() as db:
        song_count = db.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
        playlist_count = db.execute("SELECT COUNT(*) FROM playlists").fetchone()[0]
    return {"nav_song_count": song_count, "nav_playlist_count": playlist_count}

@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    with get_db() as db:
        if query:
            songs = db.execute(
                """SELECT * FROM songs
                   WHERE title LIKE ? OR artist LIKE ? OR genre LIKE ?
                   ORDER BY title COLLATE NOCASE""",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            ).fetchall()
        else:
            songs = db.execute("SELECT * FROM songs ORDER BY title COLLATE NOCASE").fetchall()
        playlists = db.execute("""
            SELECT p.*, COUNT(ps.song_id) AS song_count
            FROM playlists p LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id
            GROUP BY p.id ORDER BY p.created_at DESC
        """).fetchall()
    return render_template("index.html", songs=songs, playlists=playlists, query=query)

@app.post("/songs/add")
def add_song():
    title = request.form.get("title", "").strip()
    artist = request.form.get("artist", "").strip()
    genre = request.form.get("genre", "Other").strip() or "Other"
    duration = request.form.get("duration", "3:30").strip() or "3:30"
    if not title or not artist:
        flash("Song title and artist are required.", "error")
        return redirect(url_for("index"))
    with get_db() as db:
        db.execute(
            "INSERT INTO songs (title, artist, genre, duration) VALUES (?, ?, ?, ?)",
            (title, artist, genre, duration)
        )
    flash(f'Added “{title}” to your library.', "success")
    return redirect(url_for("index"))

@app.post("/songs/<int:song_id>/delete")
def delete_song(song_id):
    with get_db() as db:
        row = db.execute("SELECT title FROM songs WHERE id = ?", (song_id,)).fetchone()
        db.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    if row:
        flash(f'Removed “{row["title"]}” from your library.', "success")
    return redirect(request.referrer or url_for("index"))

@app.post("/playlists/create")
def create_playlist():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if not name:
        flash("Give your playlist a name first.", "error")
        return redirect(url_for("index"))
    try:
        with get_db() as db:
            db.execute("INSERT INTO playlists (name, description) VALUES (?, ?)", (name, description))
        flash(f'Playlist “{name}” created.', "success")
    except Exception:
        flash("A playlist with that name already exists.", "error")
    return redirect(url_for("index"))

@app.route("/playlists/<int:playlist_id>")
def playlist_detail(playlist_id):
    with get_db() as db:
        playlist = db.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,)).fetchone()
        if not playlist:
            flash("Playlist not found.", "error")
            return redirect(url_for("index"))
        songs = db.execute("""
            SELECT s.* FROM songs s
            JOIN playlist_songs ps ON s.id = ps.song_id
            WHERE ps.playlist_id = ?
            ORDER BY ps.added_at DESC
        """, (playlist_id,)).fetchall()
        available_songs = db.execute("""
            SELECT * FROM songs WHERE id NOT IN
            (SELECT song_id FROM playlist_songs WHERE playlist_id = ?)
            ORDER BY title COLLATE NOCASE
        """, (playlist_id,)).fetchall()
    return render_template("playlist.html", playlist=playlist, songs=songs, available_songs=available_songs)

@app.post("/playlists/<int:playlist_id>/add")
def add_to_playlist(playlist_id):
    song_id = request.form.get("song_id", type=int)
    with get_db() as db:
        exists = db.execute("SELECT id FROM playlists WHERE id = ?", (playlist_id,)).fetchone()
        song = db.execute("SELECT title FROM songs WHERE id = ?", (song_id,)).fetchone() if song_id else None
        if exists and song:
            db.execute("INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)", (playlist_id, song_id))
            flash(f'Added “{song["title"]}” to playlist.', "success")
    return redirect(url_for("playlist_detail", playlist_id=playlist_id))

@app.post("/playlists/<int:playlist_id>/remove/<int:song_id>")
def remove_from_playlist(playlist_id, song_id):
    with get_db() as db:
        db.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?", (playlist_id, song_id))
    flash("Song removed from playlist.", "success")
    return redirect(url_for("playlist_detail", playlist_id=playlist_id))

@app.post("/playlists/<int:playlist_id>/delete")
def delete_playlist(playlist_id):
    with get_db() as db:
        db.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
    flash("Playlist deleted.", "success")
    return redirect(url_for("index"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("base.html", standalone_error="That page could not be found."), 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
