from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, primary_key=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String, primary_key=True)
    books_borrowed = db.Column(db.Integer)



with app.app_context():
    db.create_all()


@app.route('/')
def home():
    title = 'Strona główna'
    context = {
    'title' : title,
               }
    return render_template('index.html', context=context)