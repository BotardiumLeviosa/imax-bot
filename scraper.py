import requests
from bs4 import BeautifulSoup
import json
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
STATE_FILE = "imax_state.json"
SHOWCASE_URL = "https://www.todoshowcase.com/"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

def get_imax_movies():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(SHOWCASE_URL, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    imax_movies = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "house_id=3250" in href or "house_id=40219" in href:
            title_tag = link.find("h2")
            if title_tag:
                title = title_tag.get_text(strip=True)
                if title and title not in imax_movies:
                    imax_movies.append(title)

    if not imax_movies:
        for item in soup.find_all(["div", "li", "article"]):
            text = item.get_text()
            if "IMAX" in text:
                h2 = item.find("h2")
                if h2:
                    title = h2.get_text(strip=True)
                    if title and title not in imax_movies:
                        imax_movies.append(title)

    return sorted(imax_movies)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"movies": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def main():
    current_movies = get_imax_movies()
    previous_state = load_state()
    previous_movies = previous_state.get("movies", [])

    new_movies = [m for m in current_movies if m not in previous_movies]
    removed_movies = [m for m in previous_movies if m not in current_movies]

    if new_movies:
        lines = ["🎬 <b>Nueva(s) función(es) IMAX en Showcase:</b>"]
        for movie in new_movies:
            lines.append(f"• {movie}")
        lines.append(f'\n🔗 <a href="{SHOWCASE_URL}">Ver cartelera</a>')
        send_telegram("\n".join(lines))

    if removed_movies:
        lines = ["📭 <b>Ya no están en cartelera IMAX:</b>"]
        for movie in removed_movies:
            lines.append(f"• {movie}")
        send_telegram("\n".join(lines))

    if not previous_movies and current_movies:
        lines = ["🎬 <b>Cartelera IMAX actual en Showcase:</b>"]
        for movie in current_movies:
            lines.append(f"• {movie}")
        lines.append(f'\n🔗 <a href="{SHOWCASE_URL}">Ver cartelera</a>')
        send_telegram("\n".join(lines))

    save_state({"movies": current_movies})
    print(f"Películas IMAX encontradas: {current_movies}")
    print(f"Nuevas: {new_movies} | Removidas: {removed_movies}")

if __name__ == "__main__":
    main()
