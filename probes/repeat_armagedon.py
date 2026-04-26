"""Probe repeat mechanics, hints, and Армагеддон."""
import httpx, json, time

BASE = "https://bar.antihype.lol"

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

# Repeat: 7 same orders + see profile favorite + responses each time
results = {"repeat": []}
with httpx.Client(timeout=20) as c:
    t = fresh(c)
    # Tip up to give buffer
    for i in range(8):
        r = call(c, "POST", "/order", headers=hdr(t), json={"name":"Куба Либре"}).json()
        prof = call(c, "GET", "/profile", headers=hdr(t)).json()
        results["repeat"].append({"i":i+1, "resp": r, "profile_fav": prof.get("favorite_drink"), "rank": prof.get("rank")})
        time.sleep(0.3)
    
    # Probe repeat_check confirm
    print("--- after 5 KL responses, prompted? Try confirm body keys ---")
    # We're at the 5th-prompt state. Try various keys.
    confirm_attempts = []
    for key in ["confirm","repeat","force","ack","accept","yes","proceed","repeat_check"]:
        rr = call(c, "POST", "/order", headers=hdr(t), json={"name":"Куба Либре", key: True}).json()
        confirm_attempts.append({"key": key, "resp": rr})
        time.sleep(0.3)
    results["confirm_attempts"] = confirm_attempts

    # Армагеддон probe (separate token)
    t2 = fresh(c)
    # Need balance > 0; do nothing else
    armag = call(c, "POST", "/mix", headers=hdr(t2), json={"ingredients":["водка","ром","текила","виски","джин"]}).json()
    results["armageddon"] = armag
    time.sleep(0.3)
    menu = call(c, "GET", "/menu", headers=hdr(t2)).json()
    results["menu_after_armag"] = menu
    profile = call(c, "GET", "/profile", headers=hdr(t2)).json()
    results["profile_after_armag"] = profile
    balance = call(c, "GET", "/balance", headers=hdr(t2)).json()
    results["balance_after_armag"] = balance
    order = call(c, "POST", "/order", headers=hdr(t2), json={"name":"Куба Либре"}).json()
    results["order_after_armag"] = order
    mix2 = call(c, "POST", "/mix", headers=hdr(t2), json={"ingredients":["джин","сок","тоник","лёд"]}).json()
    results["mix_after_armag"] = mix2

print(json.dumps(results, ensure_ascii=False, indent=2))
