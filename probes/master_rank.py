"""Probe what reaches Master rank, and prices at Master.

Also probe Crown drink (Коронный) appearance and recipe.
"""
import httpx, json, time

BASE = "https://bar.antihype.lol"
def hdr(t, x="14:30"): return {"Authorization": f"Bearer {t}", "X-Time": x}

def call(c, method, path, **kw):
    while True:
        r = c.request(method, f"{BASE}{path}", **kw)
        if r.status_code == 429:
            time.sleep(r.json().get("retry_after",5)+0.5); continue
        return r

def fresh(c):
    return call(c, "POST", "/register").json()["token"]

snapshots = []

with httpx.Client(timeout=20) as c:
    t = fresh(c)
    # Drink each unique drink one at a time and observe profile/menu changes.
    sequence = [
        ("mix", ["джин","сок","тоник","лёд"], "Зелье"),
        ("mix", ["молоко","текила","лёд"], "Ошибка"),
        ("mix", ["водка","ром","молоко"], "Мертвец"),
        ("order", "Куба Либре", None),
        ("order", "Отвёртка", None),
        ("order", "Джин-тоник", None),
        ("order", "Виски-кола", None),
        ("order", "Текила-санрайз", None),
        ("order", "Русский", None),
        ("order", "Белый русский", None),
        ("order", "Лонг-Айленд", None),
    ]
    
    # Initial snapshot
    p = call(c, "GET", "/profile", headers=hdr(t)).json()
    m = call(c, "GET", "/menu", headers=hdr(t)).json()
    snapshots.append({"step":0, "profile": p, "menu_drinks":[(d["name"],d["price"]) for d in m.get("drinks",[])]})
    
    for i, step in enumerate(sequence):
        if step[0] == "mix":
            r = call(c, "POST", "/mix", headers=hdr(t), json={"ingredients": step[1]}).json()
        else:
            # tip 100 first to fund
            call(c, "POST", "/tip", headers=hdr(t), json={"amount": 5})  # restore mood/balance
            r = call(c, "POST", "/order", headers=hdr(t), json={"name": step[1]}).json()
        prof = call(c, "GET", "/profile", headers=hdr(t)).json()
        menu = call(c, "GET", "/menu", headers=hdr(t)).json()
        snapshots.append({"step": i+1, "did": step, "resp": r, "profile": prof, "menu_drinks": [(d["name"], d["price"]) for d in menu.get("drinks", [])]})
        time.sleep(0.3)
    
    # Reset and try a different path: just orders, see when rank advances
    call(c, "POST", "/reset", headers=hdr(t))
    rank_progression = []
    drinks_to_order = ["Куба Либре","Отвёртка","Джин-тоник","Виски-кола","Текила-санрайз","Русский","Белый русский","Лонг-Айленд"]
    for d in drinks_to_order:
        # Tip to keep balance
        call(c, "POST", "/tip", headers=hdr(t), json={"amount": 1})
        r = call(c, "POST", "/order", headers=hdr(t), json={"name": d}).json()
        prof = call(c, "GET", "/profile", headers=hdr(t)).json()
        rank_progression.append({"drink": d, "resp_status": r.get("status"), "rank": prof.get("rank"), "unique": prof.get("unique_drinks"), "total": prof.get("total_orders")})
        time.sleep(0.3)
    
    print(json.dumps({"snapshots": snapshots, "rank_progression": rank_progression}, ensure_ascii=False, indent=2))
