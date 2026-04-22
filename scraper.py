import requests
from bs4 import BeautifulSoup
import json
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SHOWCASE_URL = "https://www.todoshowcase.com/"
ATLAS_URL = "https://www.atlascines.com/cartelera/cartelera"

# ─── TELEGRAM ───────────────────────────────────────────────────────────────

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

# ─── IMAX / SHOWCASE ────────────────────────────────────────────────────────

def get_imax_movies():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(SHOWCASE_URL, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    movies = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "house_id=3250" in href or "house_id=40219" in href:
            title_tag = link.find("h2")
            if title_tag:
                title = title_tag.get_text(strip=True)
                if title and title not in movies:
                    movies.append(title)

    if not movies:
        for item in soup.find_all(["div", "li", "article"]):
            if "IMAX" in item.get_text():
                h2 = item.find("h2")
                if h2:
                    title = h2.get_text(strip=True)
                    if title and title not in movies:
                        movies.append(title)

    return sorted(movies)

def check_imax():
    state_file = "imax_state.json"
    current = get_imax_movies()
    previous = json.load(open(state_file)) if os.path.exists(state_file) else {"movies": []}
    prev_movies = previous.get("movies", [])

    new = [m for m in current if m not in prev_movies]

    if new:
        lines = ["🎬 <b>IMAX Showcase — se agregaron funciones para:</b>"]
        lines += [f"• {m}" for m in new]
        lines.append(f'\n🔗 <a href="{SHOWCASE_URL}">Ver cartelera</a>')
        send_telegram("\n".join(lines))

    with open(state_file, "w") as f:
        json.dump({"movies": current}, f)

    print(f"[IMAX] Encontradas: {current} | Nuevas: {new}")

# ─── ATLAS ───────────────────────────────────────────────────────────────────

def get_atlas_movies():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(ATLAS_URL, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    movies = []
    for link in soup.find_all("a", href=True):
        if "codPelicula=" in link["href"]:
            # Buscar el tag <strong> que tiene solo el título
            strong = link.find("strong")
            if strong:
                title = strong.get_text(strip=True)
                if title and len(title) > 2 and title not in movies:
                    movies.append(title)

    return sorted(movies)

def check_atlas():
    state_file = "atlas_state.json"
    current = get_atlas_movies()
    previous = json.load(open(state_file)) if os.path.exists(state_file) else {"movies": []}
    prev_movies = previous.get("movies", [])

    new = [m for m in current if m not in prev_movies]

    if new:
        lines = ["🎬 <b>Atlas Cines — se agregaron funciones para:</b>"]
        lines += [f"• {m}" for m in new]
        lines.append(f'\n🔗 <a href="{ATLAS_URL}">Ver cartelera</a>')
        send_telegram("\n".join(lines))

    with open(state_file, "w") as f:
        json.dump({"movies": current}, f)

    print(f"[Atlas] Encontradas: {current} | Nuevas: {new}")

# ─── MAIN ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    check_imax()
    check_atlas()
