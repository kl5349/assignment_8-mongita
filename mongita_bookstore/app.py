from flask import Flask, render_template, request, redirect, url_for
from mongita import MongitaClientDisk
import os
import json

app = Flask(__name__)

# ------------------------------------------
# Mongita Setup
# ------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
client = MongitaClientDisk(os.path.join(BASE_DIR, "mongita_data"))

db = client.bookstore

# Keep your original collection names
categories_col = db.category
books_col = db.book


# ------------------------------------------
# Helper Functions
# ------------------------------------------
def get_categories():
    categories = list(categories_col.find())
    return sorted(categories, key=lambda c: c.get("categoryName", ""))


def get_books():
    books = list(books_col.find())
    return sorted(books, key=lambda b: b.get("title", ""))


def get_next_book_id():
    books = list(books_col.find())

    if not books:
        return 1

    return max(book.get("bookId", 0) for book in books) + 1


def get_category_by_id(category_id):
    return categories_col.find_one({"categoryId": category_id})


def export_json_files():
    categories = list(categories_col.find())
    books = list(books_col.find())

    for item in categories:
        item.pop("_id", None)

    for item in books:
        item.pop("_id", None)

    with open(os.path.join(BASE_DIR, "categories.json"), "w") as f:
        json.dump(categories, f, indent=2)

    with open(os.path.join(BASE_DIR, "books.json"), "w") as f:
        json.dump(books, f, indent=2)


# ------------------------------------------
# HOME PAGE
# ------------------------------------------
@app.route("/", methods=["GET"])
def home():
    categories = get_categories()
    return render_template("index.html", categories=categories)


# ------------------------------------------
# ORIGINAL CATEGORY PAGE
# ------------------------------------------
@app.route("/category", methods=["GET"])
def category():
    category_id = request.args.get("categoryId", type=int)

    categories = get_categories()
    selected_category = get_category_by_id(category_id)

    books = list(books_col.find({"categoryId": category_id}))
    books = sorted(books, key=lambda b: b.get("title", ""))

    return render_template(
        "category.html",
        categories=categories,
        selectedCategory=selected_category,
        books=books,
        searchTerm=None,
        nothingFound=False
    )


# ------------------------------------------
# ORIGINAL SEARCH
# ------------------------------------------
@app.route("/search", methods=["POST"])
def search():
    term = request.form.get("search", "").strip()

    categories = get_categories()
    all_books = list(books_col.find())

    books = [
        book for book in all_books
        if term.lower() in book.get("title", "").lower()
    ]

    books = sorted(books, key=lambda b: b.get("title", ""))

    return render_template(
        "category.html",
        categories=categories,
        selectedCategory=None,
        books=books,
        searchTerm=term,
        nothingFound=(len(books) == 0)
    )


# ------------------------------------------
# ORIGINAL BOOK DETAIL PAGE
# ------------------------------------------
@app.route("/book", methods=["GET"])
def book_detail():
    book_id = request.args.get("bookId", type=int)

    categories = get_categories()
    book = books_col.find_one({"bookId": book_id})

    if not book:
        return render_template("error.html", error="Book not found"), 404

    return render_template(
        "book_detail.html",
        book=book,
        categories=categories
    )


# ------------------------------------------
# REQUIRED ROUTE: READ ALL BOOKS
# /read
# ------------------------------------------
@app.route("/read", methods=["GET"])
def read_books():
    categories = get_categories()
    books = get_books()

    return render_template(
        "read.html",
        categories=categories,
        books=books
    )


# ------------------------------------------
# REQUIRED ROUTE: CREATE FORM
# /create
# ------------------------------------------
@app.route("/create", methods=["GET"])
def create_book():
    categories = get_categories()

    return render_template(
        "create.html",
        categories=categories
    )


# ------------------------------------------
# REQUIRED ROUTE: INSERT BOOK
# /create_post
# ------------------------------------------
@app.route("/create_post", methods=["POST"])
def create_post():
    categories = get_categories()

    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    isbn = request.form.get("isbn", "").strip()
    image = request.form.get("image", "").strip()
    category_id = request.form.get("categoryId", type=int)
    price = request.form.get("price", type=float)
    read_now = request.form.get("readNow", type=int)

    selected_category = next(
        (cat for cat in categories if cat["categoryId"] == category_id),
        None
    )

    if selected_category is None:
        return render_template(
            "error.html",
            categories=categories,
            error="Invalid category selected."
        ), 400

    new_book = {
        "bookId": get_next_book_id(),
        "categoryId": category_id,
        "categoryName": selected_category["categoryName"],
        "title": title,
        "author": author,
        "isbn": isbn,
        "price": price,
        "image": image,
        "readNow": read_now
    }

    books_col.insert_one(new_book)
    export_json_files()

    return redirect(url_for("read_books"))


# ------------------------------------------
# REQUIRED ROUTE: EDIT FORM
# /edit/<id>
# ------------------------------------------
@app.route("/edit/<int:id>", methods=["GET"])
def edit_book(id):
    categories = get_categories()
    book = books_col.find_one({"bookId": id})

    if not book:
        return render_template(
            "error.html",
            categories=categories,
            error="Book not found."
        ), 404

    return render_template(
        "edit.html",
        categories=categories,
        book=book
    )


# ------------------------------------------
# REQUIRED ROUTE: UPDATE BOOK
# /edit_post/<id>
# ------------------------------------------
@app.route("/edit_post/<int:id>", methods=["POST"])
def edit_post(id):
    categories = get_categories()

    book = books_col.find_one({"bookId": id})

    if not book:
        return render_template(
            "error.html",
            categories=categories,
            error="Book not found."
        ), 404

    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    isbn = request.form.get("isbn", "").strip()
    image = request.form.get("image", "").strip()
    category_id = request.form.get("categoryId", type=int)
    price = request.form.get("price", type=float)
    read_now = request.form.get("readNow", type=int)

    selected_category = next(
        (cat for cat in categories if cat["categoryId"] == category_id),
        None
    )

    if selected_category is None:
        return render_template(
            "error.html",
            categories=categories,
            error="Invalid category selected."
        ), 400

    updated_book = {
        "categoryId": category_id,
        "categoryName": selected_category["categoryName"],
        "title": title,
        "author": author,
        "isbn": isbn,
        "price": price,
        "image": image,
        "readNow": read_now
    }

    books_col.update_one(
        {"bookId": id},
        {"$set": updated_book}
    )

    export_json_files()

    return redirect(url_for("read_books"))


# ------------------------------------------
# REQUIRED ROUTE: DELETE BOOK
# /delete/<id>
# ------------------------------------------
@app.route("/delete/<int:id>", methods=["GET"])
def delete_book(id):
    books_col.delete_one({"bookId": id})
    export_json_files()

    return redirect(url_for("read_books"))


# ------------------------------------------
# OPTIONAL: OLD ADD-BOOK ROUTE REDIRECT
# ------------------------------------------
@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        return create_post()

    return redirect(url_for("create_book"))


# ------------------------------------------
# EXPORT JSON MANUALLY
# ------------------------------------------
@app.route("/export", methods=["GET"])
def export_data():
    export_json_files()
    return redirect(url_for("read_books"))


# ------------------------------------------
# ERRORS
# ------------------------------------------
@app.errorhandler(Exception)
def handle_error(e):
    categories = []

    try:
        categories = get_categories()
    except Exception:
        pass

    return render_template(
        "error.html",
        categories=categories,
        error=e
    ), 500


# ------------------------------------------
# RUN APP
# ------------------------------------------
if __name__ == "__main__":
    export_json_files()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
