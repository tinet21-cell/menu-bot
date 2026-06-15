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


def ask_gemini(prompt, temperature=0.7, timeout=180):
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


def generate_menu():
    prompt = (
        "Склади меню на 7 днів для двох людей. "
        "Продукти — тільки доступні в ATB, Сільпо, звичайних малих магазинах України. "
        "Бюджет на тиждень: ~2500 грн на двох. "
        "Рецепти ШВИДКІ (до 30 хвилин). Страви прості, смачні, різноманітні — без повторів щодня.\n\n"
        "ЧОЛОВІК:\n"
        "- Мета: схуднення, дефіцит калорій (~1800-2000 ккал/день)\n"
        "- 3 прийоми їжі: сніданок, обід, вечеря\n"
        "- НЕ їсть: м'ясо на кістці (тільки філе/без кісток), авокадо, заливне, бульйони\n"
        "- Включай: куряче філе, яловичина/свинина без кістки, яйця, молочне, крупи, овочі, фрукти\n\n"
        "ДРУЖИНА:\n"
        "- Мета: схуднення, інтервальне голодування 16:8 "
        "(їсть з 12:00 до 20:00, без сніданку, ~1400-1600 ккал/день)\n"
        "- 2 прийоми їжі: обід (12:00-14:00) + вечеря (18:00-20:00)\n"
        "- Любить все: м'ясо на кістці, бульйони, авокадо, рибу, овочі, фрукти\n"
        "- Порції ситніші, бо лише 2 рази на день\n\n"
        "ФОРМАТ ВІДПОВІДІ (звичайний текст, без markdown, без зірочок):\n\n"
        "МЕНЮ НА ТИЖДЕНЬ\n\n"
        "Для кожного з 7 днів:\n\n"
        "ДЕНЬ 1 — Понеділок\n\n"
        "ЧОЛОВІК:\n"
        "Сніданок: (назва страви, швидкий рецепт в 1-2 реченнях, ~X ккал)\n"
        "Обід: (назва, рецепт, ~X ккал)\n"
        "Вечеря: (назва, рецепт, ~X ккал)\n"
        "Разом: ~XXXX ккал\n\n"
        "ДРУЖИНА (16:8):\n"
        "Обід 12:00: (назва, рецепт, ~X ккал)\n"
        "Вечеря 18:00: (назва, рецепт, ~X ккал)\n"
        "Разом: ~XXXX ккал\n\n"
        "(і так для всіх 7 днів)\n\n"
        "Після 7 днів — СПИСОК ПРОДУКТІВ НА ТИЖДЕНЬ:\n\n"
        "М'ясо / риба:\n"
        "Овочі:\n"
        "Фрукти:\n"
        "Крупи / макарони / хліб:\n"
        "Молочне / яйця:\n"
        "Інше (олія, спеції, консерви тощо):\n\n"
        "Для кожного продукту — кількість (кг, шт, упаковок).\n"
        "Наприкінці: орієнтовна вартість списку (~2500 грн).\n\n"
        "Важливо: рецепти реально швидкі й прості, продукти реально доступні в Україні."
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
    try:
        menu = generate_menu()
        print(">>> Меню згенеровано", flush=True)
        send_text("🥗 МЕНЮ НА ТИЖДЕНЬ\n\n" + menu)
        print(">>> Надіслано.", flush=True)
    except Exception as e:
        print(">>> ПОМИЛКА:", e, file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    main()
