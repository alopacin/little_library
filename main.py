from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functions import load_quotes, fetch_books, save_books_to_db
import random
from datetime import timedelta, datetime
from sqlalchemy.sql.expression import func
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    current_user,
    login_user,
    logout_user,
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = "admin"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "home"


# model ksiazki
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    borrowed_at = db.Column(db.DateTime, nullable=True)
    return_by = db.Column(db.DateTime, nullable=True)

    def __str__(self):
        return f"{self.title} - {self.author}"


# model uzytkownika
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    books_borrowed = db.relationship("Book", backref="borrower", lazy=True)
    tokens = db.Column(db.Integer, default=3)

    def __repr__(self):
        return self.login


with app.app_context():
    db.create_all()
    if Book.query.count() < 100:
        books = fetch_books()
        save_books_to_db(books, Book, db)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# strona glowna
@app.route("/", methods=["GET", "POST"])
def home():
    title = "Strona główna"
    quotes = load_quotes("quotes.txt")
    quote = random.choice(quotes)

    new_user = request.form.get("nowe_konto_login")
    new_user_password = request.form.get("nowe_konto_haslo")
    check_user_name = request.form.get("logowanie_login")
    check_user_password = request.form.get("logowanie_haslo")

    if new_user and new_user_password:
        exist_user = db.session.query(User).filter_by(login=new_user).first()
        if exist_user:
            flash("Taki login jest już zajęty", "danger")
        else:
            hash_pass = generate_password_hash(
                new_user_password, method="pbkdf2:sha256"
            )
            user = User(login=new_user, password=hash_pass)
            db.session.add(user)
            db.session.commit()
            flash("Konto zostało założone, możesz się zalogować", "success")

    if check_user_name and check_user_password:
        user = db.session.query(User).filter_by(login=check_user_name).first()
        if user and check_password_hash(user.password, check_user_password):
            login_user(user)
            return redirect(url_for("account"))
        else:
            flash("Błędny login lub hasło", "danger")

    context = {
        "title": title,
        "quote": quote,
    }
    return render_template("index.html", context=context)


# strona pokazujaca naraz trzy losowe ksiazki z bazy danych
@app.route("/ksiazki")
def examples():
    title = "Książki"
    show_books = Book.query.order_by(func.random()).limit(3).all()
    context = {
        "title": title,
        "show_books": show_books,
    }
    return render_template("ksiazki.html", context=context)


# konto uzytkownika
@app.route("/konto", methods=["GET", "POST"])
@login_required
def account():
    title = "Konto"
    all_books = Book.query.filter_by(user_id=None).all()
    user_books = Book.query.filter_by(user_id=current_user.id).all()
    user_tokens = User.query.get(session.get("user_id"))
    context = {
        "title": title,
        "all_books": all_books,
        "user_books": user_books,
        "user": current_user,
        "tokens": user_tokens,
    }
    return render_template("konto.html", context=context)


# funkcja, dzieki ktorej mozna wypozyczyc ksiazki
@app.route("/borrow/<int:book_id>", methods=["GET", "POST"])
@login_required
def borrow(book_id):
    book = Book.query.get(book_id)
    if book and not book.user_id:
        if current_user.tokens > 0:
            current_user.tokens -= 1
            book.user_id = current_user.id
            book.borrowed_at = datetime.now()
            book.return_by = datetime.now() + timedelta(hours=1)
            db.session.commit()
            return redirect(url_for("account"))
        else:
            flash("Nie masz wystarczającej liczby żetonów")
            return redirect(url_for("account"))


# funkcja zwracajaca wypozyczone ksiazki
@app.route("/return/<int:book_id>", methods=["GET", "POST"])
@login_required
def return_book(book_id):
    book = Book.query.get(book_id)
    if book and book.user_id == current_user.id:
        if datetime.now() > book.return_by:
            current_user.tokens -= 5
            flash(
                "Spóźniłeś się z oddaniem książki, dlatego z Twojego konta zostało pobranych 5 żetonów"
            )
        book.user_id = None
        book.borrowed_at = None
        book.return_by = None
        db.session.commit()
    return redirect(url_for("account"))


# funkcja odpowiadajaca za wylogowanie
@app.route("/logout")
def logout():
    logout_user()
    flash("Poprawnie wylogowano", "success")
    return redirect(url_for("home"))


# funkcja, ktora dodaje zetony do konta
@app.route("/recharge", methods=["GET", "POST"])
def recharge():
    amount = int(request.form.get("amount"))
    if amount <= 0:
        flash("Nieprawidłowa wartość")
        return redirect(url_for("account"))
    else:
        current_user.tokens += amount
        db.session.commit()
        return redirect(url_for("account"))
