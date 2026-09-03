import json
import re

import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
JUNK_BULLET_RE = re.compile(r"^\s*(страница\s*)?\d{1,4}\s*\.?\s*$", re.IGNORECASE)

PROMPT = """Ты помогаешь превратить текст страницы документа в слайд презентации.
Вот текст со страницы:

\"\"\"{text}\"\"\"

Придумай короткий заголовок слайда (до 6 слов).

Затем разбей текст на пункты списка. Это НЕ пересказ и не сжатие - почти весь
смысл, факты, цифры, примеры, названия и пояснения должны остаться на месте,
просто разложенные по пунктам вместо сплошного текста. Убирать можно только:
- технический мусор PDF (номера страниц, колонтитулы, повторяющиеся
  заголовки главы, оглавление с точками и номерами страниц). Номер страницы
  никогда не должен становиться отдельным пунктом списка (например "Страница 5");
- чистую воду без смысла (вводные слова, повторы одной и той же мысли).
Если сомневаешься, убирать фразу или нет - оставляй её.
Пунктов должно быть столько, сколько нужно, чтобы не потерять смысл - для
страницы с одним абзацем может хватить 2-3 пунктов, для страницы с большим
списком или несколькими темами может понадобиться 8-10. Пункт может быть
длинным предложением, это нормально.
Ответь строго в формате JSON без пояснений и без markdown-разметки:
{{"title": "...", "bullets": ["...", "..."]}}
"""


def make_slide_content(text, model="local-model"):
    if not text.strip():
        return {"title": "", "bullets": []}

    response = requests.post(
        LM_STUDIO_URL,
        json={
            "model": model,
            "messages": [{"role": "user", "content": PROMPT.format(text=text[:6000])}],
            "temperature": 0.3,
        },
        timeout=180,
    )
    response.raise_for_status()
    reply = response.json()["choices"][0]["message"]["content"]

    return _parse_reply(reply, text)


def _parse_reply(reply, original_text):
    reply = reply.strip()
    if reply.startswith("```"):
        reply = reply.strip("`")
        if reply.startswith("json"):
            reply = reply[4:]

    try:
        data = json.loads(reply)
        bullets = [b for b in data.get("bullets", []) if not JUNK_BULLET_RE.match(b.strip())]
        return {"title": data.get("title", ""), "bullets": bullets}
    except (json.JSONDecodeError, AttributeError):
        lines = [line.strip() for line in original_text.strip().split("\n") if line.strip()]
        title = lines[0][:60] if lines else ""
        return {"title": title, "bullets": lines[:8]}
