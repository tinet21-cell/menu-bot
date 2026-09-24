import datetime
import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

print(">>> СКРИПТ СТАРТУВАВ", flush=True)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def clean_markdown(text):
    """Keep Telegram messages readable without removing recipe URLs."""
    for token in ("**", "__", "##", "# "):
        text = text.replace(token, "")
    return text.strip()


def post_json(url, payload, timeout):
    """POST JSON without requiring the non-standard requests package."""
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def api_error(error):
    """Return useful API text while keeping network errors safe to print."""
    if not isinstance(error, HTTPError):
        return str(error)
    try:
        detail = error.read().decode("utf-8")
        return f"HTTP {error.code}: {detail}"
    except OSError:
        return f"HTTP {error.code}: {error.reason}"


def ask_gemini(prompt, temperature=0.2, timeout=180):
    """Ask Gemini to research recipes with Google Search grounding enabled."""
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": temperature},
    }
    last = None
    for _ in range(3):
        try:
            url = f"{GEMINI_URL}?{urlencode({'key': GEMINI_API_KEY})}"
            response = post_json(url, body, timeout)
            text = response["candidates"][0]["content"]["parts"][0]["text"]
            return clean_markdown(text)
        except (HTTPError, URLError, OSError, KeyError, IndexError, ValueError) as error:
            last = api_error(error)
            time.sleep(6)
    raise RuntimeError(f"Gemini не повернув рецепт після 3 спроб: {last}")


def menu_period():
    today = datetime.date.today()
    weekday = today.weekday()
    week_num = today.isocalendar()[1]

    if today.month in (12, 1, 2):
        season = "зима"
        seasonal = "картопля, буряк, морква, капуста, цибуля, часник, бобові, яблука"
    elif today.month in (3, 4, 5):
        season = "весна"
        seasonal = "молода картопля, редис, зелена цибуля, шпинат, щавель, яйця, зелень"
    elif today.month in (6, 7, 8):
        season = "літо"
        seasonal = "томати, огірки, кабачки, перець, баклажани, кукурудза, зелень, ягоди"
    else:
        season = "осінь"
        seasonal = "гарбуз, яблука, гриби, буряк, морква, капуста, картопля, квасоля"

    if weekday == 0:
        return "пн-чт", "Понеділок, вівторок, середа, четвер", 4, week_num, season, seasonal
    return "пт-нд", "П'ятниця, субота, неділя", 3, week_num, season, seasonal


def generate_menu():
    short, days, number_of_days, week_num, season, seasonal = menu_period()
    prompt = f"""
Ти — уважний редактор меню, а не автор вигаданих рецептів. За допомогою пошуку
підбери {number_of_days} РЕАЛЬНИХ, уже опублікованих рецептів: по одній повноцінній
страві на кожен день ({days}) для двох дорослих. Тиждень №{week_num}, сезон — {season}.

Критерії «найкращого» рецепта:
1. Рецепт має походити з конкретного надійного кулінарного джерела, яке ти знайшов.
   Не вигадуй назву, склад, пропорції чи техніку. Для КОЖНОГО дня дай пряме URL-посилання
   на першоджерело. Якщо точного рецепта не знайдено, не замінюй його фантазією — підбери інший.
2. Це одна реальна основна страва, а не меню зі сніданку, обіду й вечері, і не набір
   окремих гарніру, салату та м'яса. У самій страві мають бути прості доступні продукти,
   джерело білка, овочі та ситний компонент. Приклад прийнятного формату: картопляний
   гратен з білковим компонентом та овочами.
3. Страви повинні бути домашніми, поживними, бюджетними та готуватися з продуктів,
   доступних у звичайному українському магазині. Віддай перевагу сезонним продуктам:
   {seasonal}. Не використовуй авокадо, екзотичні або важкодоступні інгредієнти.
4. Обирай різні основні джерела білка в різні дні (наприклад, бобові, яйця, риба,
   курка, індичка або кисломолочний сир). Не називай приблизні калорії чи білок, якщо
   їх немає в джерелі.

Звір інгредієнти й кроки з джерелом. Можна лише адаптувати кількості на 2 порції,
чітко позначивши це як «кількості перераховано на 2 порції»; не додавай нових інгредієнтів.

Пиши українською, звичайним текстом без Markdown, у ТОЧНО такій структурі:

МЕНЮ НА {short.upper()} — одна страва на день

ДЕНЬ 1 — [назва страви]
Чому обрано: [одне коротке речення про поживність, простоту і сезонність].
Джерело рецепта: [назва сайту] — [прямий URL]
На 2 порції: [точний список інгредієнтів з кількостями].
Покроково:
1. [дія] — X хв.
2. [дія] — X хв.
[усі наступні кроки, кожен з тривалістю]
Час: підготовка X хв, приготування X хв, разом X хв.

[повтори блок для кожного дня]

СПИСОК ПРОДУКТІВ НА {short.upper()}
[зведи лише продукти з вибраних рецептів за категоріями та з кількостями]

Не вигадуй посилань. Не додавай інших страв, перекусів, планів харчування чи загальних
порад. Не пропускай хвилини у жодному кроці.
""".strip()
    return ask_gemini(prompt)


def split_text(text, limit=4000):
    text = text.strip()
    if len(text) <= limit:
        return [text]
    parts = []
    while len(text) > limit:
        chunk = text[:limit]
        cut = chunk.rfind("\n\n")
        if cut < limit * 0.5:
            cut = chunk.rfind("\n")
        if cut < limit * 0.5:
            cut = chunk.rfind(". ")
            if cut != -1:
                cut += 1
        if cut < limit * 0.5:
            cut = limit
        parts.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        parts.append(text)
    return parts


def send_text(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    last = None
    for part in split_text(text, 4000):
        last = post_json(
            url,
            {"chat_id": CHAT_ID, "text": part, "disable_web_page_preview": True},
            timeout=30,
        )
        time.sleep(1)
    return last


def main():
    print(">>> MAIN ПОЧАВСЯ", flush=True)
    short, days, _, week_num, season, _ = menu_period()
    print(f">>> Тиждень {week_num}, {season}", flush=True)
    print(f">>> Шукаю рецепти: {short} ({days})", flush=True)
    try:
        menu = generate_menu()
        print(">>> Рецепти підібрано", flush=True)
        send_text(f"🍲 МЕНЮ {short.upper()} — ОДНА СТРАВА НА ДЕНЬ\n\n{menu}")
        print(">>> Надіслано.", flush=True)
    except Exception as error:
        print(">>> ПОМИЛКА:", error, file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    main()
