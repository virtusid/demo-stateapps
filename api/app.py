from flask import Flask, jsonify, request, render_template
import os
import redis
import psycopg2
import psycopg2.extras
import socket

app = Flask(__name__)

# Redis connection
def get_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=6379,
        decode_responses=True
    )

# PostgreSQL connection
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=5432,
        dbname=os.getenv("DB_NAME", "demo"),
        user=os.getenv("DB_USER", "demo"),
        password=os.getenv("DB_PASSWORD", "demo")
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/info")
def info():
    return jsonify({
        "pod": socket.gethostname(),
        "version": "1.0.0"
    })

@app.route("/api/notes", methods=["GET"])
def get_notes():
    r = get_redis()
    cached = r.get("notes_cache")
    if cached:
        return jsonify({"source": "cache", "data": eval(cached)})

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM notes ORDER BY created_at DESC")
    notes = [dict(row) for row in cur.fetchall()]
    for note in notes:
        note["created_at"] = str(note["created_at"])
    cur.close()
    conn.close()

    r.setex("notes_cache", 30, str(notes))
    return jsonify({"source": "database", "data": notes})

@app.route("/api/notes", methods=["POST"])
def create_note():
    content = request.json.get("content", "")
    if not content:
        return jsonify({"error": "content required"}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("INSERT INTO notes (content) VALUES (%s) RETURNING *", (content,))
    note = dict(cur.fetchone())
    note["created_at"] = str(note["created_at"])
    conn.commit()
    cur.close()
    conn.close()

    get_redis().delete("notes_cache")
    return jsonify(note), 201

@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
    conn.commit()
    cur.close()
    conn.close()

    get_redis().delete("notes_cache")
    return jsonify({"deleted": note_id})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8081)))
