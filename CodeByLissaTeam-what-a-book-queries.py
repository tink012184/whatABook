
from pymongo.mongo_client import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb+srv://")
db = client["what-a-book"]

# Collections
books = db["books"]
customers = db["customers"]
wishlist_items = db["wishlist_items"]

# Display all books
for book in books.find(): 
    print(book)

# Search by genre list of books
genre = "Sci-Fi"
for book in books.find({"genre": genre}):
    print(book)

# Search list of books by author
author = "A.Writer" 
for book in books.find({"author": author}):
    print(book)

# Search by bookId
book_id = "b1001"
book = books.find_one({"bookId": book_id})
print(book)

# Search wishlist by customerId
customer_id = "c1007"
wishlist = wishlist_items.aggregate([
    {"$match": {"customerId": customer_id}},
    {"$lookup": {
        "from": "books",
        "localField": "bookId",
        "foreignField": "bookId",
        "as": "bookDetails"
    }}
])

for item in wishlist:
    print(item)

# Add book to wishlist

wishlist_items.insert_one({
    "customerId": "c1007",
    "bookId": "b1001"
})
print("Book added to wishlist.")

# Remove book from wishlist
wishlist_items.delete_one({
    "customerId": "c1007",
    "bookId": "b1001"
})
print("Book removed from wishlist.")