// seed_whatabook.js

db.books.drop();
db.customers.drop();
db.wishlistitems.drop();

db.books.insertMany([
  {
    bookId: "b1001",
    title: "The Cozy Mystery",
    author: "A. Writer",
    genre: "Mystery",
  },
  {
    bookId: "b1002",
    title: "Space Trails",
    author: "B. Nova",
    genre: "Sci-Fi",
  },
  {
    bookId: "b1003",
    title: "Cakes & Clues",
    author: "A. Writer",
    genre: "Mystery",
  },
  {
    bookId: "b1004",
    title: "Gardens of Time",
    author: "C. Green",
    genre: "Non-Fiction",
  },
]);

db.customers.insertMany([
  { customerId: "c1007", firstName: "Diane", lastName: "Harper" },
  { customerId: "c1008", firstName: "Marco", lastName: "Alvarez" },
  { customerId: "c1009", firstName: "Sharon", lastName: "Lee" },
]);

db.wishlistitems.insertMany([
  { customerId: "c1007", bookId: "b1001" },
  { customerId: "c1008", bookId: "b1002" },
  { customerId: "c1009", bookId: "b1003" },
]);
