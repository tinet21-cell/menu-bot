import os
import sys
import time
import datetime
import requests

print(">>> СКРИПТ СТАРТУВАВ", flush=True)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def clean_markdown(text):
    for token in ("**", "__", "##", "# "):
        text = text.replace(token, "")
    return text.strip()


def ask_gemini(prompt, temperature=0.8, timeout=180):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}}
    last = None
    for _ in range(3):
        try:
            r = requests.post(GEMINI_URL, params={"key": GEMINI_API_KEY},
                              json=body, timeout=timeout)
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            return clean_markdown(text)
        except Exception as e:
            last = e
            time.sleep(6)
    raise last


def which_half():
    today = datetime.date.today()
    day = today.weekday()
    week_num = today.isocalendar()[1]
    month = today.month
    year = today.year

    if month in [12, 1, 2]:
        season = "зима"
        seasonal = (
            "буряк, морква, капуста, цибуля, часник, картопля, "
            "яблука, квашені овочі, бобові, гриби сушені"
        )
    elif month in [3, 4, 5]:
        season = "весна"
        seasonal = (
            "молода картопля, редис, зелена цибуля, шпинат, щавель, "
            "петрушка, кріп, перші огірки, яйця"
        )
    elif month in [6, 7, 8]:
        season = "літо"
        seasonal = (
            "томати, огірки, кабачки, баклажани, перець, кукурудза, "
            "зелень, персики, черешня, абрикоси, кавун, ягоди"
        )
    else:
        season = "осінь"
        seasonal = (
            "гарбуз, кабачок, яблука, груші, буряк, морква, "
            "капуста, гриби, картопля, квасоля"
        )

    cuisines = [
        "українська домашня (борщ, голубці, деруни, вареники, бігус, юшка)",
        "середземноморська адаптована (запечені овочі, риба, оливкова олія, часник, зелень)",
        "азійська адаптована (рис, соєвий соус, імбир, яйця, курка, овочі)",
        "слов'янська (капусняк, розсольник, картопляні страви, тушковане м'ясо, млинці)",
        "бюджетна білкова (яйця, бобові, риба консервована, сир, сочевиця, нут)",
        "запечене і тушковане (м'ясо в духовці, овочеві запіканки, рагу, фарш)",
    ]
    cuisine = cuisines[week_num % len(cuisines)]

    if day == 0:
        return ("пн-чт", "Понеділок, Вівторок, Середа, Четвер",
                4, "1200", week_num, year, season, seasonal, cuisine)
    else:
        return ("пт-нд", "П'ятниця, Субота, Неділя",
                3, "900", week_num, year, season, seasonal, cuisine)


def generate_menu():
    short, days, n, budget, week_num, year, season, seasonal, cuisine = which_half()

    prompt = (
        f"Склади меню на {n} дні ({days}) для двох людей — чоловіка і дружини.\n"
        f"Тиждень №{week_num} року {year}. Сезон: {season}.\n\n"

        "РІЗНОМАНІТНІСТЬ — ГОЛОВНА ВИМОГА:\n"
        f"— Кухня цього тижня: {cuisine}. Страви мають відповідати цьому стилю.\n"
        f"— Сезонні інгредієнти (використовуй обов'язково): {seasonal}.\n"
        f"— Тиждень №{week_num} — меню МАЄ бути інше ніж попередні тижні. "
        "Придумуй нові страви, не повторюй стандартний набір.\n"
        "— СУВОРО ЗАБОРОНЕНО: куряча грудка з гречкою або рисом як безіменна страва; "
        "безіменні «овочеві салати»; «макарони з фаршем» без назви. "
        "Кожна страва має конкретну назву.\n\n"

        "ДОМАШНІ БЮДЖЕТНІ СТРАВИ:\n"
        "Борщ, капусняк, розсольник, юшка, суп-пюре, харчо, солянка;\n"
        "Котлети, биточки, гречаники, тефтелі, голубці;\n"
        "Деруни, вареники, млинці з начинкою;\n"
        "Запечене м'ясо або риба з овочами в духовці;\n"
        "Рагу, бігус, плов, лазанья з доступних продуктів;\n"
        "Яйця по-різному: яєчня, пашот, фаршировані, запечені;\n"
        "Риба смажена, тушкована, запечена;\n"
        "Страви з бобових: квасоля, сочевиця, нут.\n\n"

        "ПРИНЦИПИ НУТРИЦІОЛОГА:\n"
        "— Білок + овочі + складний вуглевод або жир у кожному прийомі\n"
        "— Різні джерела білка щодня: курка, яловичина, риба, яйця, бобові, індичка\n"
        "— Мінімум 2 різних супи за ці дні\n"
        "— Вівсянки немає взагалі\n"
        "— Продукти лише з ATB, Сільпо, звичайних магазинів\n\n"

        "ЧОЛОВІК:\n"
        "— Схуднення, дефіцит ~1800-2000 ккал/день\n"
        "— 3 прийоми: сніданок, обід, вечеря\n"
        "— НЕ їсть: м'ясо на кістці, авокадо, заливне, прозорі бульйони\n"
        "— Якщо суп — густий (борщ, капусняк, гороховий, суп із крупою)\n\n"

        "ДРУЖИНА:\n"
        "— Інтервальне голодування 16:8, їсть з 12:00 до 20:00, сніданку НЕМАЄ\n"
        "— 2 прийоми: обід о 12:00 + вечеря о 18:00\n"
        "— Любить все: м'ясо на кістці, наваристі супи, рибу, авокадо\n"
        "— Мінімум 25-30г білка на кожен прийом, ~1400-1600 ккал/день\n\n"

        f"БЮДЖЕТ: ~{budget} грн на двох на ці {n} дні "
        "(реалістично для ATB/Сільпо).\n\n"

        "ФОРМАТ (звичайний текст, без зірочок, без markdown):\n\n"
        f"МЕНЮ НА {short.upper()} (тиждень {week_num}, {season})\n"
        f"Кухня тижня: {cuisine.split('(')[0].strip()}\n\n"

        f"Для кожного з {n} днів:\n\n"
        "ДЕНЬ X — Назва дня\n\n"
        "ЧОЛОВІК:\n"
        "Сніданок: [Назва страви] — [рецепт 1-2 речення] (~XXX ккал, білок XXг)\n"
        "Обід: [Назва страви] — [рецепт 1-2 речення] (~XXX ккал, білок XXг)\n"
        "Вечеря: [Назва страви] — [рецепт 1-2 речення] (~XXX ккал, білок XXг)\n"
        "Разом: ~XXXX ккал\n\n"
        "ДРУЖИНА (16:8, їсть з 12:00):\n"
        "Обід 12:00: [Назва страви] — [рецепт 1-2 речення] (~XXX ккал, білок XXг)\n"
        "Вечеря 18:00: [Назва страви] — [рецепт 1-2 речення] (~XXX ккал, білок XXг)\n"
        "Разом: ~XXXX ккал\n\n"
        "[і так для кожного дня]\n\n"
        f"СПИСОК ПРОДУКТІВ НА {short.upper()}:\n"
        "(тільки що потрібно для цього конкретного меню, з кількостями)\n\n"
        "М'ясо / риба / птиця:\n"
        "Овочі та зелень:\n"
        "Фрукти:\n"
        "Крупи / макарони / хліб:\n"
        "Молочне / яйця:\n"
        "Консерви / заморозка:\n"
        "Інше (олія, спеції, соуси):\n\n"
        f"Орієнтовна вартість: ~XXXX грн\n\n"
        "Порада тижня: [нутриціологічна порада специфічна для цього сезону і меню]"
    )
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
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": part,
                                     "disable_web_page_preview": True},
                          timeout=30)
        r.raise_for_status()
        last = r.json()
        time.sleep(1)
    return last


def main():
    print(">>> MAIN ПОЧАВСЯ", flush=True)
    short, days, n, budget, week_num, year, season, seasonal, cuisine = which_half()
    print(f">>> Тиждень {week_num}, {season}, кухня: {cuisine.split('(')[0].strip()}", flush=True)
    print(f">>> Генерую меню: {short} ({days})", flush=True)
    try:
        menu = generate_menu()
        print(">>> Меню згенеровано", flush=True)
        header = f"🥗 МЕНЮ {short.upper()} + СПИСОК ПРОДУКТІВ\n\n"
        send_text(header + menu)
        print(">>> Надіслано.", flush=True)
    except Exception as e:
        print(">>> ПОМИЛКА:", e, file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    main()
