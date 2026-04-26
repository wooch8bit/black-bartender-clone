# Black Bartender clone

Behavioural clone of `https://bar.antihype.lol` for AntiHack 2026 (Ufa).

The service implements 10 endpoints (`/register`, `/reset`, `/menu`, `/order`, `/mix`,
`/history`, `/profile`, `/balance`, `/tip`, `/secret`) along with all hidden mechanics
(mood scoring, ranks, secret drinks, repeat cycle with favorite + free_every_7th, X-Time
day/night, hints, Crown drink, Армагеддон bar closure).

## Run

```bash
docker build -t bar .
docker run --rm -p 8000:8000 bar
```

The service listens on `0.0.0.0:8000` and serves `application/json`.

## Tests

* `tests/test_smoke.py` — local in-process smoke tests (12 cases).
* `tests/test_diff_live.py` — differential tests that hit `bar.antihype.lol` and the local
  clone in lockstep, asserting identical JSON bodies and status codes. Skipped automatically
  when the live API is unreachable. Set `LIVE_DIFF=0` to skip explicitly.

```bash
pip install -e ".[dev]"
pytest tests/
```

## Mechanics summary

| Mechanic | Probed value |
| --- | --- |
| Mood thresholds | hostile<20, grumpy<40, normal<60, friendly<80, generous≥80; clamp [0, 98] |
| Δmood per drink | most −2; Русский −5; Лонг-Айленд +3; Ошибка mood=98; Армагеддон mood=0; Мертвец −32 (floor 0) |
| Mix discount | base price − 2 (then mood multiplier) |
| Mood multipliers | hostile ×1.5 ⌈⌉, grumpy ×1.2 ⌈⌉, normal ×1, friendly ×0.9 ⌊⌋, generous ×0.75 ⌊⌋ |
| Favorite price | floor(base × 0.8), mood-independent |
| Repeat cycle | counter 4–6 → favorite:true; counter 4 → next call returns prompt:"repeat_check"; counter 6 → next call free_every_7th; counter resets after free |
| Generous-free | every 3rd successful order/mix in generous → price 0 |
| Hints | success_counter 8/9/10 (free_every_7th does not advance) |
| Ranks | unique_drinks 0–2 Новичок, 3–4 Гость, 5–7 Постоянный, 8–10 Знаток, 11+ Мастер |
| X-Time | parse `int(HH) % 24`; night=[0,5], day=[6,23]; default day on parse error |

## Project layout

```
app/
  auth.py        # 3-form Authorization, detail-wrapped 401
  core.py        # shared order/mix logic (favorite, repeat, hints, generous-free)
  crown.py       # Master-only Crown ingredient formula
  drinks.py      # public drink catalog + secret recipes
  effects.py     # secret drink effect application
  hints.py       # hint table (#8/#9/#10)
  models.py      # Pydantic request schemas (raw 422 on schema errors)
  mood.py        # scoring thresholds and per-drink Δmood
  pricing.py     # base prices + mood multipliers + mix discount
  ranks.py       # unique_drinks → rank thresholds
  routes/        # 10 endpoint routes
  state.py       # per-token BarState
  storage.py     # in-memory token store with asyncio.Lock
  xtime.py       # X-Time parser
```
