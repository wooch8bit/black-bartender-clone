"""Compare /mix vs /order pricing in friendly/generous moods (where notes hint /mix is cheaper)."""
import httpx, json, time

BASE = "https://bar.antihype.lol"

DRINKS = [
    ("Куба Либре",     ["ром","кола","лёд"]),
    ("Отвёртка",       ["водка","сок"]),
    ("Джин-тоник",     ["джин","тоник","лёд"]),
    ("Виски-кола",     ["виски","кола"]),
    ("Текила-санрайз", ["текила","сок"]),
    ("Русский",        ["водка","лёд"]),
    ("Белый русский",  ["водка","лёд","молоко"]),
    ("Лонг-Айленд",    ["водка","джин","кола","ром","текила"]),
]

def hdr(t, x="14:30"):
    return {"Authorization": f"Bearer {t}", "X-Time": x}

def call(c, method, path, **kw):
    while True:
        r = c.request(method, f"{BASE}{path}", **kw)
        if r.status_code == 429:
            time.sleep(r.json().get("retry_after",5)+0.5); continue
        return r

def fresh(c):
    return call(c, "POST", "/register").json()["token"]

def set_mood(c, t, mood):
    if mood == "generous":
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients":["молоко","текила","лёд"]})
    elif mood == "friendly":
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients":["молоко","текила","лёд"]})
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients":["водка","ром","молоко"]})
    elif mood == "grumpy":
        for _ in range(3):
            call(c, "POST", "/mix", headers=hdr(t), json={"ingredients":["сок","ром"]})
    elif mood == "hostile":
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients":["джин","сок","тоник","лёд"]})
        call(c, "POST", "/mix", headers=hdr(t), json={"ingredients":["водка","ром","молоко"]})

# For each mood, fresh token; then probe /mix prices for each drink (taking one at a time on separate tokens)
res = {}
with httpx.Client(timeout=20) as c:
    for mood in ["normal","grumpy","hostile","friendly","generous"]:
        for drink, ings in DRINKS:
            t = fresh(c)
            set_mood(c, t, mood)
            order = call(c, "POST", "/order", headers=hdr(t), json={"name": drink}).json()
            t2 = fresh(c)
            set_mood(c, t2, mood)
            mix = call(c, "POST", "/mix", headers=hdr(t2), json={"ingredients": ings}).json()
            res[f"{mood}|{drink}"] = {"order_price": order.get("price"), "mix_price": mix.get("price"), "order_status": order.get("status"), "mix_status": mix.get("status")}
            time.sleep(0.3)
print(json.dumps(res, ensure_ascii=False, indent=2))
