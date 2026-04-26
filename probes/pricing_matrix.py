"""Probe pricing matrix carefully, respecting rate limits."""
import httpx, json, time

BASE = "https://bar.antihype.lol"

DRINKS_DAY = [
    ("Куба Либре",      ["ром", "кола", "лёд"]),
    ("Отвёртка",        ["водка", "сок"]),
    ("Джин-тоник",      ["джин", "тоник", "лёд"]),
    ("Виски-кола",      ["виски", "кола"]),
    ("Текила-санрайз",  ["текила", "сок"]),
    ("Русский",         ["водка", "лёд"]),
    ("Белый русский",   ["водка", "лёд", "молоко"]),
    ("Лонг-Айленд",     ["водка", "джин", "кола", "ром", "текила"]),
]
DRINKS_NIGHT = [
    ("Ночной русский",  ["водка", "лёд", "молоко"]),
    ("Бессонница",      ["кола", "ром", "тоник"]),
    ("Лунный свет",     ["джин", "сок", "тоник"]),
]

def hdr(t, x="14:30"):
    return {"Authorization": f"Bearer {t}", "X-Time": x}

def call(c, method, path, **kw):
    while True:
        r = c.request(method, f"{BASE}{path}", **kw)
        if r.status_code == 429:
            j = r.json()
            time.sleep(j.get("retry_after", 5) + 0.5)
            continue
        return r

def fresh(c):
    return call(c, "POST", "/register").json()["token"]

def set_mood(c, t, mood):
    if mood == "normal":
        return
    if mood == "grumpy":
        for _ in range(3):
            call(c, "POST", "/mix", headers=hdr(t), json={"ingredients": ["сок","ром"]})
    elif mood == "hostile":
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients": ["джин","сок","тоник","лёд"]})
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients": ["водка","ром","молоко"]})
    elif mood == "generous":
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients": ["молоко","текила","лёд"]})
    elif mood == "friendly":
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients": ["молоко","текила","лёд"]})
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients": ["водка","ром","молоко"]})

# Strategy: register one token per (mood). Use /menu only — its prices match what /order would charge.
results = {}
with httpx.Client(timeout=20) as c:
    for mood in ["normal","grumpy","hostile","generous","friendly"]:
        for x_time, label in [("14:30","day"),("02:30","night")]:
            t = fresh(c)
            set_mood(c, t, mood)
            menu = call(c, "GET", "/menu", headers=hdr(t, x_time)).json()
            results[f"{mood}|{label}"] = menu
            time.sleep(0.5)

print(json.dumps(results, ensure_ascii=False, indent=2))
