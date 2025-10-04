# api_server.py
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://web335_user:s3cret@computer.3dociam.mongodb.net/?retryWrites=true&w=majority&appName=Computer")
DB_NAME = os.getenv("WHATABOOK_DB", "whatabook")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "prototype")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app)

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.get("/api/books")
def get_books():
    db = get_db()
    genre = request.args.get("genre")
    author = request.args.get("author")
    title = request.args.get("title")
    bookId = request.args.get("bookId")
    q = {}
    if genre: q["genre"] = genre
    if author: q["author"] = author
    if bookId: q["bookId"] = bookId
    if title: q["title"] = {"$regex": title, "$options": "i"}
    items = list(db.books.find(q, {"_id": 0}).sort("title", 1))
    return jsonify(items)

@app.get("/api/wishlist")
def get_wishlist():
    db = get_db()
    customerId = request.args.get("customerId")
    if not customerId:
        return jsonify({"error": "customerId required"}), 400
    pipeline = [
        {"$match": {"customerId": customerId}},
        {"$lookup": {
            "from": "books",
            "localField": "bookId",
            "foreignField": "bookId",
            "as": "book"
        }},
        {"$unwind": "$book"},
        {"$project": {"_id": 0, "bookId": 1, "title": "$book.title", "author": "$book.author", "genre": "$book.genre"}}
    ]
    items = list(db.wishlistitems.aggregate(pipeline))
    return jsonify(items)

@app.post("/api/wishlist")
def add_wishlist():
    db = get_db()
    data = request.get_json(silent=True) or {}
    customerId = data.get("customerId")
    bookId = data.get("bookId")
    if not customerId or not bookId:
        return jsonify({"error": "customerId and bookId required"}), 400
    if not db.customers.find_one({"customerId": customerId}):
        return jsonify({"error": "Invalid customerId"}), 400
    if not db.books.find_one({"bookId": bookId}):
        return jsonify({"error": "Invalid bookId"}), 400
    if db.wishlistitems.find_one({"customerId": customerId, "bookId": bookId}):
        return jsonify({"ok": True, "message": "Already on wishlist"})
    db.wishlistitems.insert_one({"customerId": customerId, "bookId": bookId})
    return jsonify({"ok": True})

@app.delete("/api/wishlist")
def remove_wishlist():
    db = get_db()
    data = request.get_json(silent=True) or {}
    customerId = data.get("customerId")
    bookId = data.get("bookId")
    if not customerId or not bookId:
        return jsonify({"error": "customerId and bookId required"}), 400
    r = db.wishlistitems.delete_one({"customerId": customerId, "bookId": bookId})
    return jsonify({"ok": True, "deleted": r.deleted_count})

@app.get("/<path:path>")
def static_proxy(path):
    return send_from_directory(STATIC_DIR, path)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
