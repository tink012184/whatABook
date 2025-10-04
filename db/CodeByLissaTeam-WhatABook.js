// CodeByLissaTeam-WhatABook.js
// WhatABook required queries with comments and code attribution
// Author: Code By Lissa Team (Lumi the Quill Fox)
// Date: 2025-10-03
// Description: MongoDB queries for the WhatABook project.

// 1) Display a list of books.
db.books.find({}, { _id: 0 }).sort({ title: 1 });

// 2) Display a list of books by genre (replace <GENRE> with a value).
db.books.find({ genre: "<GENRE>" }, { _id: 0 }).sort({ title: 1 });

// 3) Display a list of books by author (replace <AUTHOR>).
db.books.find({ author: "<AUTHOR>" }, { _id: 0 }).sort({ title: 1 });

// 4) Display a book by bookId (replace <BOOKID>).
db.books.findOne({ bookId: "<BOOKID>" }, { _id: 0 });

// 5) Display a wishlist by customerId (join wishlistitems -> books).
db.wishlistitems.aggregate([
  { $match: { customerId: "<CUSTOMERID>" } },
  {
    $lookup: {
      from: "books",
      localField: "bookId",
      foreignField: "bookId",
      as: "book",
    },
  },
  { $unwind: "$book" },
  {
    $project: {
      _id: 0,
      customerId: 1,
      bookId: 1,
      title: "$book.title",
      author: "$book.author",
      genre: "$book.genre",
    },
  },
]);

// 6) Add books to a customer’s wishlist (replace <CUSTOMERID>, <BOOKID>).
db.wishlistitems.insertOne({ customerId: "<CUSTOMERID>", bookId: "<BOOKID>" });

// 7) Remove book from a customer’s wishlist (replace <CUSTOMERID>, <BOOKID>).
db.wishlistitems.deleteOne({ customerId: "<CUSTOMERID>", bookId: "<BOOKID>" });
