from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functions import load_quotes, fetch_books, save_books_to_db
import random
from sqlalchemy.sql.expression import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'admin'


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __str__(self):
        return f'{self.title} - {self.author}'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    books_borrowed = db.relationship('Book', backref='borrower', lazy=True)


with app.app_context():
    db.create_all()
    if Book.query.count() < 250:
        books = fetch_books()
        save_books_to_db(books, Book, db)


def get_current_user():
    user_id = session.get('user_id')
    if user_id is None:
        return None
    return User.query.get(user_id)


@app.route('/', methods=['GET', 'POST'])
def home():
    title = 'Strona główna'
    message1 = None
    message2 = None
    message3 = None
    quotes = load_quotes('quotes.txt')
    quote = random.choice(quotes)

    new_user = request.form.get('nowe_konto_login')
    new_user_password = request.form.get('nowe_konto_haslo')
    check_user_name = request.form.get('logowanie_login')
    check_user_password = request.form.get('logowanie_haslo')

    if new_user and new_user_password:
        exist_user = db.session.query(User).filter_by(login=new_user).first()
        if exist_user:
            message1 = 'Taki login jest już zajęty'
        else:
            hash_pass = generate_password_hash(new_user_password, method='pbkdf2:sha256')
            user = User(login=new_user, password=hash_pass)
            db.session.add(user)
            db.session.commit()
            message3 = 'Konto zostało założone, możesz się zalogować'

    if check_user_name and check_user_password:
        user = db.session.query(User).filter_by(login=check_user_name).first()
        if user and check_password_hash(user.password, check_user_password):
            session['user_id'] = user.id
            return redirect(url_for('account'))
        else:
            message2 = 'Błędny login lub hasło'

    context = {
        'title': title,
        'message1': message1,
        'message2': message2,
        'message3': message3,
        'quote': quote,
                   }
    return render_template('index.html', context=context)


@app.route('/ksiazki')
def examples():
    title = 'Książki'
    show_books = Book.query.order_by(func.random()).limit(3).all()
    context = {
        'title': title,
        'show_books': show_books,
    }
    return render_template('ksiazki.html', context=context)


@app.route('/konto', methods=['GET', 'POST'])
def account():
    title = 'Konto'
    all_books = Book.query.filter_by(user_id=None).all()
    context = {
        'title': title,
        'all_books': all_books
    }
    return render_template('konto.html', context=context)


@app.route('/borrow/<int:book_id>', methods=['GET', 'POST'])
def borrow_book(book_id):
    current_user = get_current_user()
    book = Book.query.get(book_id)
    if book and not book.user_id:
        current_user = get_current_user()
        book.user_id = current_user.id
        db.session.commit()
        return redirect(url_for('account'))
    else:
        return "Książka jest już wypożyczona", 400


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Poprawnie wylogowano')
    return redirect(url_for('home'))


