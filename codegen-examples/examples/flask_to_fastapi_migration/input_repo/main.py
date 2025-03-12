from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Mock Data
books = [
    {"id": 1, "title": "Book One", "author": "Author A", "category": "Fiction"},
    {"id": 2, "title": "Book Two", "author": "Author B", "category": "Non-Fiction"},
]

authors = ["Author A", "Author B", "Author C"]
categories = ["Fiction", "Non-Fiction", "Biography"]

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

# Books Page
@app.route("/books", methods=["GET"])
def get_books():
    return render_template("books.html", books=books)

@app.route("/books", methods=["POST"])
def add_book():
    data = request.json
    books.append(data)
    return jsonify(data), 201

@app.route("/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    data = request.json
    for book in books:
        if book["id"] == book_id:
            book.update(data)
            return jsonify(book)
    return jsonify({"error": "Book not found"}), 404

@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    global books
    books = [book for book in books if book["id"] != book_id]
    return jsonify({"message": "Book deleted"})

# Authors Page
@app.route("/authors", methods=["GET"])
def get_authors():
    return render_template("authors.html", authors=authors)

@app.route("/authors", methods=["POST"])
def add_author():
    data = request.json
    authors.append(data["name"])
    return jsonify({"name": data["name"]}), 201

# Categories Page
@app.route("/categories", methods=["GET"])
def get_categories():
    return render_template("categories.html", categories=categories)

@app.route("/categories", methods=["POST"])
def add_category():
    data = request.json
    categories.append(data["name"])
    return jsonify({"name": data["name"]}), 201

if __name__ == "__main__":
    app.run(debug=True)
