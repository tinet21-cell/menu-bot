import os
import sys
import time
import requests

print(">>> СКРИПТ СТАРТУВАВ", flush=True)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def ask_gemini(prompt, temperature=0.8, timeout=180):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}}
    last = None
    for _ in range(3):
        try:
            r = requests.post(GEMINI_URL, params={"key": GEMINI_API_KEY},
                              json=body, timeout=timeout)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            last = e
            time.sleep(6)
    raise last


def which_half():
    """Понеділок = перша половина тижня (пн-чт), Середа/інше = друга (чт-нд)."""
    day = time.localtime().tm_wday  # 0=пн, 2=ср
    if day == 0:
        return "перша", "Понеділок, Вівторок, Середа, Четвер", "пн-чт"
    else:
        return "друга", "Четвер, П'ятниця, Субота, Неділя", "чт-нд"


def generate_menu():
    half, days, short = which_half()

    prompt = (
        f"Склади меню на 4 дні ({days}) для двох людей — чоловіка і дружини. "
        "Це {'перша' if half == 'перша' else 'друга'} половина тижня.\n\n"

        "ВАЖЛИВО ПРО РЕЦЕПТИ:\n"
        "— Використовуй РЕАЛЬНІ, конкретні страви з назвами (борщ, капусняк, "
        "гречаники, тушкована картопля з м'ясом, омлет по-флорентійськи, "
        "курка в сметані, рибні котлети, фаршировані перці, паста карбонара тощо).\n"
        "— НЕ вигадуй абстрактних «куряче з рисом» без конкретики.\n"
        "— Рецепти прості й швидкі (до 30 хвилин), але справжні.\n"
        "— Страви РІЗНОМАНІТНІ — жодних повторів протягом 4 днів.\n"
        "— Обов'язково: хоча б 2 супи за 4 дні (різні — борщ, капусняк, "
        "суп-пюре, юшка, розсольник, гороховий, томатний тощо).\n"
        "— НЕ давай вівсянку взагалі.\n"
        "— Продукти тільки з ATB, Сільпо, звичайних магазинів України.\n\n"

        "ЧОЛОВІК:\n"
        "— Мета: схуднення, дефіцит калорій (~1800-2000 ккал/день)\n"
        "— 3 прийоми: сніданок, обід, вечеря\n"
        "— НЕ їсть: м'ясо на кістці (тільки філе/без кісток), авокадо, "
        "заливне, бульйони як окрема страва\n"
        "— Якщо суп — то густий (з крупою, бобовими, овочами), не прозорий бульйон\n"
        "— Порції помірні, без надлишку жирів\n\n"

        "ДРУЖИНА:\n"
        "— Мета: схуднення, інтервальне голодування 16:8 "
        "(їсть з 12:00 до 20:00, сніданку НЕМАЄ)\n"
        "— 2 прийоми: обід (12:00-14:00) + вечеря (18:00-20:00)\n"
        "— Любить: м'ясо на кістці, бульйони, супи будь-які включно з наваристими, "
        "рибу, морепродукти, авокадо\n"
        "— Порції ситніші — лише 2 рази на день\n"
        "— ~1400-1600 ккал/день\n\n"

        "БЮДЖЕТ: ~1200 грн на двох на ці 4 дні (реалістично для ATB/Сільпо).\n\n"

        "ФОРМАТ (звичайний текст, без зірочок і markdown):\n\n"

        f"МЕНЮ НА {short.upper()}\n\n"

        "Для кожного з 4 днів:\n\n"
        "ДЕНЬ X — Назва дня\n\n"
        "ЧОЛОВІК:\n"
        "Сніданок: [Назва страви] — [рецепт 1-2 речення, конкретно] (~XXX ккал)\n"
        "Обід: [Назва страви] — [рецепт] (~XXX ккал)\n"
        "Вечеря: [Назва страви] — [рецепт] (~XXX ккал)\n"
        "Разом: ~XXXX ккал\n\n"
        "ДРУЖИНА (16:8, їсть з 12:00):\n"
        "Обід 12:00: [Назва страви] — [рецепт] (~XXX ккал)\n"
        "Вечеря 18:00: [Назва страви] — [рецепт] (~XXX ккал)\n"
        "Разом: ~XXXX ккал\n\n"
        "[і так для всіх 4 днів]\n\n"

        "СПИСОК ПРОДУКТІВ НА ЦІ 4 ДНІ:\n"
        "(тільки те, що потрібно саме для цього меню, з кількостями)\n\n"
        "М'ясо / риба / птиця:\n"
        "Овочі:\n"
        "Фрукти:\n"
        "Крупи / макарони / хліб:\n"
        "Молочне / яйця:\n"
        "Консерви / заморозка:\n"
        "Інше (олія, спеції, соуси тощо):\n\n"
        "Орієнтовна вартість: ~XXXX грн\n\n"
        "Порада на ці дні: [1 коротка практична порада — наприклад, "
        "що приготувати наперед або як зекономити час]"
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
                                     "disable_web_page_preview": True}, timeout=30)
        r.raise_for_status()
        last = r.json()
        time.sleep(1)
    return last


def main():
    print(">>> MAIN ПОЧАВСЯ", flush=True)
    half, days, short = which_half()
    print(f">>> Генерую меню: {half} половина ({short})", flush=True)
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
