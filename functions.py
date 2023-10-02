import requests


def load_quotes(f):
    with open(f, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]


def fetch_books(limit=1000):
    url = "https://gutendex.com/books"
    params = {
        'random': 'true',
        'limit': limit
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return []



