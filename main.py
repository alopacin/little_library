from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functions import load_quotes, fetch_books
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    books_borrowed = db.Column(db.Integer, nullable=True)


with app.app_context():
    db.create_all()


 def save_books_to_db(books):
    for book_data in books:
        book = Book(title=book_data['results'][0]['title'],author=book_data['authors'][0]['name'])
        db.session.add(book)
        db.session.commit()

    save_books_to_db(books)

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
    context = {
        'title': title,
    }
    return render_template('ksiazki.html', context=context)


@app.route('/konto', methods=['GET', 'POST'])
def account():
    title = 'Konto'
    context = {
        'title': title,
    }

    return render_template('konto.html', context=context)

