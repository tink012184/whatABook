# api_server.py
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# --- Config ---
MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("WHATABOOK_DB", "whatabook").strip() or "whatabook"
STATIC_DIR = os.path.join(os.path.dirname(__file__), "prototype")

if not MONGO_URI:
    # Fail fast in prod so you don't accidentally run with a bad/empty URI
    raise RuntimeError("MONGO_URI is not set. Configure it in your hosting env variables.")

# --- App ---
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
# If frontend and API are same origin, CORS is optional. Safe to leave enabled.
CORS(app)

# --- DB (single, shared client) ---
_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
_db = _client[DB_NAME]

def db():
    return _db

# --- Routes ---
@app.get("/healthz")
def healthz():
    # Lightweight health check (no heavy DB ops)
    return jsonify(ok=True)

@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.get("/api/books")
def get_books():
    try:
        q = {}
        genre = request.args.get("genre")
        author = request.args.get("author")
        title = request.args.get("title")
        bookId = request.args.get("bookId")

        if genre: q["genre"] = genre
        if author: q["author"] = author
        if bookId: q["bookId"] = bookId
        if title: q["title"] = {"$regex": title, "$options": "i"}

        items = list(db().books.find(q, {"_id": 0}).sort("title", 1))
        return jsonify(items)
    except PyMongoError as e:
        return jsonify(error="Database error", details=str(e)), 500

@app.get("/api/wishlist")
def get_wishlist():
    customerId = request.args.get("customerId")
    if not customerId:
        return jsonify(error="customerId required"), 400

    try:
        pipeline = [
            {"$match": {"customerId": customerId}},
            {"$lookup": {
                "from": "books",
                "localField": "bookId",
                "foreignField": "bookId",
                "as": "book"
            }},
            {"$unwind": "$book"},
            {"$project": {
                "_id": 0,
                "bookId": 1,
                "title": "$book.title",
                "author": "$book.author",
                "genre": "$book.genre"
            }},
            {"$sort": {"title": 1}}
        ]
        items = list(db().wishlistitems.aggregate(pipeline))
        return jsonify(items)
    except PyMongoError as e:
        return jsonify(error="Database error", details=str(e)), 500

@app.post("/api/wishlist")
def add_wishlist():
    data = request.get_json(silent=True) or {}
    customerId = data.get("customerId")
    bookId = data.get("bookId")
    if not customerId or not bookId:
        return jsonify(error="customerId and bookId required"), 400

    try:
        if not db().customers.find_one({"customerId": customerId}):
            return jsonify(error="Invalid customerId"), 400
        if not db().books.find_one({"bookId": bookId}):
            return jsonify(error="Invalid bookId"), 400
        if db().wishlistitems.find_one({"customerId": customerId, "bookId": bookId}):
            return jsonify(ok=True, message="Already on wishlist")
        db().wishlistitems.insert_one({"customerId": customerId, "bookId": bookId})
        return jsonify(ok=True)
    except PyMongoError as e:
        return jsonify(error="Database error", details=str(e)), 500

@app.delete("/api/wishlist")
def remove_wishlist():
    data = request.get_json(silent=True) or {}
    customerId = data.get("customerId")
    bookId = data.get("bookId")
    if not customerId or not bookId:
        return jsonify(error="customerId and bookId required"), 400

    try:
        r = db().wishlistitems.delete_one({"customerId": customerId, "bookId": bookId})
        return jsonify(ok=True, deleted=r.deleted_count)
    except PyMongoError as e:
        return jsonify(error="Database error", details=str(e)), 500

@app.get("/<path:path>")
def static_proxy(path):
    # Serve everything in /prototype (index, books, genres, wishlist, assets)
    return send_from_directory(STATIC_DIR, path)

# --- Fallback JSON error handler ---
@app.errorhandler(Exception)
def handle_any_error(err):
    # Return JSON for unexpected errors (keeps logs clean for hosts)
    return jsonify(error=str(err)), 500

if __name__ == "__main__":
    # For local dev. Hosts like Render/Cloud Run will set $PORT and hand off to Gunicorn.
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
