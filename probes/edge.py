"""Probe miscellaneous edge cases.

Goals:
  1. /tip: amount = 0, negative, float, missing field, > balance, normal positive
  2. X-Time edge cases (24:00, 99:99, ab:cd, missing)
  3. /menu day=8 drinks (no night drinks even if /menu day) — confirmed already
  4. Воздух in history
  5. Армагеддон reopens_at format & timing (probe two in succession)
  6. Hints — probe successive successful actions to find when hints fire
  7. invalid_ingredient body shape
  8. unknown_drink response
  9. method=GET on /order, etc → 404 or 405?
  10. /history balance/mood_level keys
"""
import httpx, json, time
from datetime import datetime, timezone, timedelta

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

results = {}
with httpx.Client(timeout=20) as c:
    t = fresh(c)
    
    # Tips
    tips_results = []
    for body in [{"amount": 5}, {"amount": 0}, {"amount": -5}, {"amount": 1.5}, {"amount": "5"}, {"amount": 99999}, {"amount": 200}, {}, {"amount": None}]:
        r = call(c, "POST", "/tip", headers=hdr(t), json=body)
        tips_results.append({"req": body, "status": r.status_code, "resp": r.json() if r.headers.get("content-type","").startswith("application/json") else r.text})
        time.sleep(0.4)
    results["tips"] = tips_results
    
    # X-Time
    t2 = fresh(c)
    time_results = {}
    for x in ["", "24:00", "99:99", "ab:cd", "06:60", "-1:00", "100:00", "123:45", "00:00", "05:59"]:
        r = call(c, "GET", "/menu", headers=hdr(t2, x))
        d = r.json()
        time_results[x] = {"first_drink": d.get("drinks",[{}])[0].get("name") if "drinks" in d else None, "status": d.get("status"), "drinks_count": len(d.get("drinks", []))}
        time.sleep(0.3)
    # Missing X-Time entirely
    r = call(c, "GET", "/menu", headers={"Authorization": f"Bearer {t2}"})
    d = r.json()
    time_results["__missing__"] = {"first_drink": d.get("drinks",[{}])[0].get("name") if "drinks" in d else None, "drinks_count": len(d.get("drinks", []))}
    results["xtime"] = time_results
    
    # Method on wrong endpoint
    rmeth = {}
    rmeth["get_order"] = (call(c, "GET", "/order", headers=hdr(t2)).status_code,)
    rmeth["post_balance"] = (call(c, "POST", "/balance", headers=hdr(t2)).status_code,)
    rmeth["post_secret"] = (call(c, "POST", "/secret", headers=hdr(t2)).status_code,)
    rmeth["get_register"] = (call(c, "GET", "/register").status_code,)
    rmeth["nonexistent"] = (call(c, "GET", "/health").status_code,)
    rmeth["post_health"] = (call(c, "POST", "/health").status_code,)
    rmeth["docs"] = (call(c, "GET", "/docs").status_code,)
    rmeth["openapi"] = (call(c, "GET", "/openapi.json").status_code,)
    results["methods"] = rmeth
    
    # Validation: missing field, wrong type
    rv = {}
    rv["order_no_body"] = call(c, "POST", "/order", headers=hdr(t2)).status_code
    rv["order_empty"] = (call(c, "POST", "/order", headers=hdr(t2), json={}).status_code, call(c, "POST", "/order", headers=hdr(t2), json={}).text)
    rv["mix_no_ing"] = (call(c, "POST", "/mix", headers=hdr(t2), json={}).status_code, call(c, "POST", "/mix", headers=hdr(t2), json={}).text)
    rv["mix_str_ing"] = (call(c, "POST", "/mix", headers=hdr(t2), json={"ingredients":"abc"}).status_code, call(c, "POST", "/mix", headers=hdr(t2), json={"ingredients":"abc"}).text)
    rv["order_int_name"] = (call(c, "POST", "/order", headers=hdr(t2), json={"name": 5}).status_code, call(c, "POST", "/order", headers=hdr(t2), json={"name": 5}).text)
    results["validation"] = rv
    
    # Mix dup ingredients
    t3 = fresh(c)
    rmix_dup = {}
    rmix_dup["dup_kuba"] = call(c, "POST", "/mix", headers=hdr(t3), json={"ingredients":["ром","кола","лёд","лёд","лёд"]}).json()
    rmix_dup["reorder_kuba"] = call(c, "POST", "/mix", headers=hdr(t3), json={"ingredients":["лёд","ром","кола"]}).json()
    rmix_dup["mostly_invalid"] = call(c, "POST", "/mix", headers=hdr(t3), json={"ingredients":["xxx","yyy"]}).json()
    rmix_dup["mixed_invalid"] = call(c, "POST", "/mix", headers=hdr(t3), json={"ingredients":["водка","xxx"]}).json()
    rmix_dup["normalized"] = call(c, "POST", "/mix", headers=hdr(t3), json={"ingredients":["лед"]}).json()
    rmix_dup["empty_str"] = call(c, "POST", "/mix", headers=hdr(t3), json={"ingredients":[""]}).json()
    results["mix_dup"] = rmix_dup
    
print(json.dumps(results, ensure_ascii=False, indent=2))
