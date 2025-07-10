# ✨ Add “Quick-Win” Metrics (Wall-Clock ⏱, Token Cost 💰, Clarification Count ❔)

> Capture three objective metrics with **\~30 LoC** and **zero refactor** of business logic.\
> This lets us quote hard numbers ("built in 175 s, \$0.03 tokens, 2 clarifications") in the paper.

---

## 🎯 Acceptance Criteria

-

---

## 🛠️ Implementation Steps

### 1 – Create Metrics Helper

`baes/utils/metrics_tracker.py`

```python
"""
Thread-safe helper for logging quick metrics.
"""

from pathlib import Path
from time import time
import json, threading, os

_METRICS = {
    "total_wall_seconds": 0.0,
    "clarification_prompts": 0,
    "openai_tokens_in": 0,
    "openai_tokens_out": 0,
}
_LOCK = threading.Lock()
_LOG_FILE = Path(os.getenv("BAE_METRICS_LOG", "logs/metrics.jsonl"))
_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def add_time(delta: float):             # ⏱
    with _LOCK:
        _METRICS["total_wall_seconds"] += delta


def add_tokens(inp: int, out: int):     # 💰
    with _LOCK:
        _METRICS["openai_tokens_in"]  += inp
        _METRICS["openai_tokens_out"] += out


def inc_clarification():                # ❔
    with _LOCK:
        _METRICS["clarification_prompts"] += 1


def flush_snapshot():
    """Write one JSON line with cumulative metrics."""
    with _LOCK:
        _LOG_FILE.write_text(json.dumps(_METRICS, indent=2) + "\n", append=True)
```

---

### 2 – Patch Call‑Sites

```diff
@@
-from datetime import datetime
-from ...
-start_time = datetime.now()
+from time import time
+from baes.utils.metrics_tracker import add_time
+start_ts = time()
 ...
-result = self.kernel.process_natural_language_request(...)
-add_time((datetime.now() - start_time).total_seconds())
+result = self.kernel.process_natural_language_request(...)
+add_time(time() - start_ts)
```

```diff
 def _request_user_clarification(...):
     ...
+    from baes.utils.metrics_tracker import inc_clarification
+    inc_clarification()
```

```python
response = client.chat.completions.create(...)
from baes.utils.metrics_tracker import add_tokens
add_tokens(response.usage.prompt_tokens, response.usage.completion_tokens)
```

*Place in each SWEA or helper that hits the OpenAI API.*

---

### 3 – Flush on Exit

At the end of the CLI shutdown handler:

```python
from baes.utils.metrics_tracker import flush_snapshot
flush_snapshot()
```

---

## 🧪 How to Test

```bash
python bae_chat.py          # run PoC stages
jq . logs/metrics.jsonl     # pretty-print metrics
```

Expected JSON example:

```json
{
  "total_wall_seconds": 174.9,
  "clarification_prompts": 2,
  "openai_tokens_in": 4721,
  "openai_tokens_out": 1230
}
```

---

## ➕ Future Enhancements (out‑of‑scope for this issue)

- Track developer IDE time to derive "hours saved"
- Log GPU/CPU energy for sustainability metrics
- Export CSV for plotting in evaluation scripts

---

*Estimated effort: ****< 1 hour**** of coding + test run.*

