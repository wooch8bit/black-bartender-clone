"""Helpers to put a fresh token into a target mood / rank.

Mood states reachable on a fresh token:
  - normal   (50)  → fresh, do nothing
  - hostile  (16)  → Zelie + Mertvets1 (50 - 2 - 32 = 16)
  - generous (98)  → Oshibka (sets to 98)
  - friendly (66)  → Oshibka + Mertvets (98 - 32 = 66)
  - grumpy   (≈30) → Oshibka + Mertvets + ~7× unknown_recipe (66 -5*7? clamps at 0); use Oshibka + 14× unknown? Actually start fresh and unknown_recipe many times: 50 -5n
                     n=3: 35 grumpy  ✓
"""
import httpx, json, sys

BASE = "https://bar.antihype.lol"

def fresh_token(c: httpx.Client) -> str:
    r = c.post(f"{BASE}/register")
    return r.json()["token"]

def hdr(t: str, x_time: str = "14:30") -> dict:
    return {"Authorization": f"Bearer {t}", "X-Time": x_time}

def to_normal(c, t):
    pass

def to_grumpy(c, t):
    # unknown_recipe (-5) × 3 → 35 grumpy
    for _ in range(3):
        c.post(f"{BASE}/mix", headers=hdr(t), json={"ingredients": ["сок", "ром"]})

def to_hostile(c, t):
    # Zelie (-2) → 48 normal; Mertvets (-32) → 16 hostile
    c.post(f"{BASE}/mix", headers=hdr(t), json={"ingredients": ["джин", "сок", "тоник", "лёд"]})
    c.post(f"{BASE}/mix", headers=hdr(t), json={"ingredients": ["водка", "ром", "молоко"]})

def to_generous(c, t):
    # Oshibka → 98
    c.post(f"{BASE}/mix", headers=hdr(t), json={"ingredients": ["молоко", "текила", "лёд"]})

def to_friendly(c, t):
    # Oshibka (98) + Mertvets (-32) = 66 friendly
    c.post(f"{BASE}/mix", headers=hdr(t), json={"ingredients": ["молоко", "текила", "лёд"]})
    c.post(f"{BASE}/mix", headers=hdr(t), json={"ingredients": ["водка", "ром", "молоко"]})

# Verify mood
def secret_mood(c, t):
    return c.get(f"{BASE}/secret", headers=hdr(t)).json()

if __name__ == "__main__":
    with httpx.Client(timeout=10) as c:
        for name, fn in [("normal", to_normal), ("grumpy", to_grumpy), ("hostile", to_hostile), ("generous", to_generous), ("friendly", to_friendly)]:
            t = fresh_token(c)
            # need to unlock /secret first to read mood
            c.post(f"{BASE}/mix", headers=hdr(t), json={"ingredients": ["джин", "сок", "тоник", "лёд"]})
            fn(c, t)
            print(name, c.get(f"{BASE}/balance", headers=hdr(t)).json(), c.get(f"{BASE}/secret", headers=hdr(t)).json())
