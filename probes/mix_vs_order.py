"""Compare /mix and /order prices for the same drink across moods."""
import httpx, json, time

BASE = "https://bar.antihype.lol"
def hdr(t,x="14:30"): return {"Authorization": f"Bearer {t}", "X-Time": x}

def call(c,m,p,**kw):
    while True:
        r = c.request(m,f"{BASE}{p}",**kw)
        if r.status_code==429: time.sleep(r.json().get("retry_after",5)+0.5); continue
        return r

def fresh(c): return call(c,"POST","/register").json()["token"]

DRINKS = ["Куба Либре","Отвёртка","Джин-тоник","Виски-кола","Текила-санрайз","Русский","Белый русский","Лонг-Айленд"]
RECIPES = {
    "Куба Либре": ["ром","кола","лёд"],
    "Отвёртка": ["водка","сок"],
    "Джин-тоник": ["джин","тоник","лёд"],
    "Виски-кола": ["виски","кола"],
    "Текила-санрайз": ["текила","сок"],
    "Русский": ["водка","лёд"],
    "Белый русский": ["водка","лёд","молоко"],
    "Лонг-Айленд": ["водка","джин","кола","ром","текила"],
}

# For each mood, fresh token + tip-mix to set the mood, then ONE order then ONE mix per drink (skipping repeat).
# Strategy: keep moods distinct by using Voздух (-2) to hostile, Ошибка (mood max) for generous.

results = {}

with httpx.Client(timeout=20) as c:
    # GENEROUS = mood 98
    t = fresh(c)
    call(c,"POST","/mix",headers=hdr(t),json={"ingredients":["молоко","текила","лёд"]})  # Ошибка
    # Mood is now 98 (generous). For each drink: 1 order, 1 mix. But generous_free fires every 3rd.
    # Easier: separate token per drink.
    out = {"generous_order": {}, "generous_mix": {}}
    # Try setup once then test KL only first (to avoid generous_free)
    for d in DRINKS:
        t = fresh(c)
        call(c,"POST","/mix",headers=hdr(t),json={"ingredients":["молоко","текила","лёд"]})  # Ошибка
        # ORDER price
        r = call(c,"POST","/order",headers=hdr(t),json={"name":d}).json()
        out["generous_order"][d] = r.get("price"); time.sleep(0.4)
        # Fresh again for MIX
        t = fresh(c)
        call(c,"POST","/mix",headers=hdr(t),json={"ingredients":["молоко","текила","лёд"]})  # Ошибка
        r = call(c,"POST","/mix",headers=hdr(t),json={"ingredients":RECIPES[d]}).json()
        out["generous_mix"][d] = r.get("price"); time.sleep(0.4)
    results.update(out)
    print(json.dumps(out, ensure_ascii=False))
    
    # FRIENDLY: tip 10 once = mood 60
    out = {"friendly_order": {}, "friendly_mix": {}}
    for d in DRINKS:
        t = fresh(c)
        call(c,"POST","/tip",headers=hdr(t),json={"amount":10})  # mood 60 friendly
        r = call(c,"POST","/order",headers=hdr(t),json={"name":d}).json()
        out["friendly_order"][d] = r.get("price"); time.sleep(0.4)
        t = fresh(c)
        call(c,"POST","/tip",headers=hdr(t),json={"amount":10})
        r = call(c,"POST","/mix",headers=hdr(t),json={"ingredients":RECIPES[d]}).json()
        out["friendly_mix"][d] = r.get("price"); time.sleep(0.4)
    results.update(out)
    print(json.dumps(out, ensure_ascii=False))

    # NORMAL (50)
    out = {"normal_order": {}, "normal_mix": {}}
    for d in DRINKS:
        t = fresh(c)
        r = call(c,"POST","/order",headers=hdr(t),json={"name":d}).json()
        out["normal_order"][d] = r.get("price"); time.sleep(0.4)
        t = fresh(c)
        r = call(c,"POST","/mix",headers=hdr(t),json={"ingredients":RECIPES[d]}).json()
        out["normal_mix"][d] = r.get("price"); time.sleep(0.4)
    results.update(out)
    print(json.dumps(out, ensure_ascii=False))

    # GRUMPY (mood 30): drop 5 unknown_recipes (each -5) from 50 → 25
    def make_grumpy(c, t):
        # unknown_recipe drops mood 5; need 4 to reach 30 from 50.
        for _ in range(4):
            call(c,"POST","/mix",headers=hdr(t),json={"ingredients":["сок","ром"]})
    out = {"grumpy_order": {}, "grumpy_mix": {}}
    for d in DRINKS:
        t = fresh(c)
        make_grumpy(c, t)
        r = call(c,"POST","/order",headers=hdr(t),json={"name":d}).json()
        out["grumpy_order"][d] = r.get("price"); time.sleep(0.4)
        t = fresh(c)
        make_grumpy(c, t)
        r = call(c,"POST","/mix",headers=hdr(t),json={"ingredients":RECIPES[d]}).json()
        out["grumpy_mix"][d] = r.get("price"); time.sleep(0.4)
    results.update(out)
    print(json.dumps(out, ensure_ascii=False))

with open("/home/ubuntu/black-bartender-clone/probes/mix_vs_order.json","w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("DONE")
