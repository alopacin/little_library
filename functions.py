import requests


def load_quotes(f):
    with open(f, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]


def fetch_books(limit=250):
    base_url = "https://gutendex.com/books"
    params = {
        'random': 'true',
        'limit': limit
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        books = response.json()['results']
        processed_books = []
        for book in books:
            title = book.get('title')
            if 'authors' in book and book['authors'] and 'name' in book['authors'][0]:
                author = book['authors'][0]['name']
            else:
                author = "Nieznany autor"
            processed_books.append({'title': title, 'author': author})
        return processed_books
    else:
        print(f"Error {response.status_code}: {response.text}")
        return []


def save_books_to_db(books, book_model, db):
    for book in books:
        book = book_model(title=book['title'], author=book['author'])
        db.session.add(book)
    db.session.commit()



