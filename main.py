from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, primary_key=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String, unique=True, primary_key=True)
    password = db.Column(db.String, nullable=False)
    books_borrowed = db.Column(db.Integer)


with app.app_context():
    db.create_all()


@app.route('/', methods=['GET', 'POST'])
def home():
    title = 'Strona główna'

    if request.method == 'POST':
        new_user = request.form.get('nowe_konto_login')
        new_user_password = request.form.get('nowe_konto_haslo')
        check_user_name = request.form.get('logowanie_login')
        check_user_password = request.form.get('logowanie_haslo')

        if new_user and new_user_password:
            hash_pass = generate_password_hash(new_user_password, method='sha256')
            user = User(login=new_user, password=hash_pass)
            db.session.add(user)
            db.session.commit()
            redirect(url_for('konto'))

        if check_user_name and check_user_password:
            user = db.session.query(User).filter_by(login=check_user_name).first()
            if user and check_password_hash(user.password, check_user_password):
                redirect(url_for('konto'))

    context = {
    'title' : title,
                   }
    return render_template('index.html', context=context)