"""
Title: CodeByLissaTeam-what-a-book-console.py
Author: Melissa Lutz and Leslie Khattarchebli (Code by Lissa)
Date: 2025-10-12
Description:
    Console app for the WhatABook project that:
      1) Connects to MongoDB
      2) Displays a list of books (cleanly formatted)
      3) Displays a list of books by Genre (with a selectable menu)
      4) Displays a customer's wishlist by customerId
      5) Adds basic error handling for invalid customerId (c1007, c1008, c1009)
"""

from __future__ import annotations

import os
import sys
from typing import List, Dict, Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError


# ------------------------------
# Connection Helpers
# ------------------------------
def get_mongo_client() -> MongoClient:
    """
    Get a connected MongoClient.
    Prefers MONGO_URI from env; otherwise prompts the user to paste a URI.
    """
    uri = os.getenv("MONGO_URI", "mongodb+srv://web335Admin:s3cret@computer.3dociam.mongodb.net/web335DB?retryWrites=true&w=majority").strip()
    if not uri:
        print("Enter your MongoDB connection string (MONGO_URI).")
        print("Example (Atlas): mongodb+srv://<user>:<pass>@<cluster>/?retryWrites=true&w=majority")
        uri = input("> ").strip()

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        # Ping to verify
        client.admin.command("ping")
        return client
    except Exception as e:
        print(f"[FATAL] Could not connect to MongoDB: {e}")
        sys.exit(1)


def get_collections(client: MongoClient):
    """
    Return (books, customers, wishlist_items) collections from the DB.
    DB name uses whatabook.
    """
    db_name = os.getenv("WHATABOOK", "whatabook").strip() or "whatabook"
    db = client[db_name]
    return db["books"], db["customers"], db["wishlist_items"]


# ------------------------------
# UI Helpers
# ------------------------------
def print_table(rows: List[Dict[str, Any]], headers: List[str]) -> None:
    """
    Pretty-prints a list of dictionaries as a simple table.
    Only fields listed in `headers` will be printed, in order.
    """
    if not rows:
        print("(no results)")
        return

    # Compute column widths from headers & row values
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, key in enumerate(headers):
            col_widths[i] = max(col_widths[i], len(str(row.get(key, ""))))

    # Build format strings
    fmt = " | ".join("{:<" + str(w) + "}" for w in col_widths)
    sep = "-+-".join("-" * w for w in col_widths)

    # Print header
    print(fmt.format(*headers))
    print(sep)

    # Print rows
    for row in rows:
        print(fmt.format(*(str(row.get(k, "")) for k in headers)))
    print()  # trailing newline


def pause() -> None:
    input("\nPress Enter to continue...")


# ------------------------------
# Features
# ------------------------------
def list_all_books(books_col) -> None:
    """
    Display all books with a clean table format.
    """
    try:
        cursor = books_col.find(
            {},
            {
                "_id": 0,
                "bookId": 1,
                "title": 1,
                "author": 1,
                "genre": 1,
            },
        ).sort([("title", 1)])
        rows = list(cursor)
        print("\nAll Books")
        print_table(rows, headers=["bookId", "title", "author", "genre"])
    except PyMongoError as e:
        print(f"[ERROR] Failed to list books: {e}")


def list_books_by_genre(books_col) -> None:
    """
    Prompt the user to select a genre from distinct values, then display books in that genre.
    """
    try:
        genres = sorted([g for g in books_col.distinct("genre") if g])
        if not genres:
            print("No genres found (books collection may be empty).")
            return

        print("\nSelect a Genre:")
        for idx, g in enumerate(genres, start=1):
            print(f"  {idx}) {g}")
        choice = input("Pick a genre by number or type the genre name: ").strip()

        if choice.isdigit():
            idx = int(choice)
            selected = genres[idx - 1] if 1 <= idx <= len(genres) else None
        else:
            selected = next((g for g in genres if g.lower() == choice.lower()), None)

        if not selected:
            print("Invalid selection.")
            return

        cursor = books_col.find(
            {"genre": selected},
            {
                "_id": 0,
                "bookId": 1,
                "title": 1,
                "author": 1,
                "genre": 1,
            },
        ).sort([("title", 1)])
        rows = list(cursor)
        print(f"\nBooks in Genre: {selected}")
        print_table(rows, headers=["bookId", "title", "author", "genre"])
    except PyMongoError as e:
        print(f"[ERROR] Failed to list books by genre: {e}")


def show_wishlist(wishlist_col, customer_id: str) -> None:
    """
    Display a customer's wishlist by customerId.
    Requirement expects IDs: c1007, c1008, c1009.
    Includes basic error handling for invalid IDs.
    """
    valid_ids = {"c1007", "c1008", "c1009"}
    if customer_id not in valid_ids:
        print("Invalid customerId. Please enter one of: c1007, c1008, c1009.")
        return

    try:
        pipeline = [
            {"$match": {"customerId": customer_id}},
            {
                "$lookup": {
                    "from": "books",
                    "localField": "bookId",
                    "foreignField": "bookId",
                    "as": "book",
                }
            },
            {"$unwind": "$book"},
            {"$replaceRoot": {"newRoot": "$book"}},
            {
                "$project": {
                    "_id": 0,
                    "bookId": 1,
                    "title": 1,
                    "author": 1,
                    "genre": 1,
                }
            },
            {"$sort": {"title": 1}},
        ]

        rows = list(wishlist_col.aggregate(pipeline))
        print(f"\nWishlist for {customer_id}")
        if not rows:
            print("(wishlist is empty)\n")
            return
        print_table(rows, headers=["bookId", "title", "author", "genre"])
    except PyMongoError as e:
        print(f"[ERROR] Failed to show wishlist: {e}")


# ------------------------------
# Menu Loop
# ------------------------------
def main() -> None:
    client = get_mongo_client()
    books_col, customers_col, wishlist_col = get_collections(client)

    while True:
        print("\n=== WhatABook Console ===")
        print("  1) List all books")
        print("  2) List books by genre")
        print("  3) Show customer's wishlist")
        print("  4) Exit")
        choice = input("> ").strip()

        if choice == "1":
            list_all_books(books_col)
            pause()
        elif choice == "2":
            list_books_by_genre(books_col)
            pause()
        elif choice == "3":
            cid = input("Enter customerId (c1007, c1008, c1009): ").strip()
            show_wishlist(wishlist_col, cid)
            pause()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose 1–4.")
            pause()


if __name__ == "__main__":
    main()
