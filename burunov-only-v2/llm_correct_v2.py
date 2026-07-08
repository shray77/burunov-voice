#!/usr/bin/env python3
"""
LLM-коррекция Whisper-текстов через Z.AI chat completions.
Поскольку ASR rate-limited, используем LLM для исправления текста.
LLM получает Whisper-текст + контекст и переписывает его осмысленно.
"""

import json
import time
import sys
import urllib.request
import urllib.error
from pathlib import Path

MANIFEST = Path("/home/z/burunov-v2/manifest.json")
OUT_DIR = Path("/home/z/burunov-v2/transcripts_llm")
OUT_DIR.mkdir(parents=True, exist_ok=True)

start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
batch = int(sys.argv[2]) if len(sys.argv) > 2 else 1

config = json.loads(open('/etc/.z-ai-config').read())

with open(MANIFEST) as f:
    manifest = json.load(f)

end = min(start + batch, len(manifest))

SYSTEM_PROMPT = """Ты — корректор расшифровки русской речи из интервью актёра Сергея Бурунова.

Тебе даётся текст от автоматического распознавания речи (Whisper), которое часто ошибается на разговорной речи: галлюцинирует, пропускает слова, вставляет бессмыслицу.

КОНТЕКСТ: Это интервью Сергея Бурунова (актёр дубляжа, озвучил Гринч, Фиксики). Разговор о кино, карьере, Голливуде, личной жизни. Бурунова интервьюирует женщина-ведущая.

ТВОЯ ЗАДАЧА:
1. Восстанови осмысленный русский текст по смыслу
2. Исправь явные ошибки распознавания (нереальные слова, обрывки)
3. Восстанови пунктуацию и регистр
4. Если текст — полная бессмыслица и невозможно восстановить смысл, напиши [неразборчиво]

ПРАВИЛА:
- Сохрани стиль разговорной речи (можно оставить "ну", "вот", "типа")
- НЕ добавляй слова от себя
- НЕ сокращай
- Имена: Бурунов, Нагиев, Ургант, Харламов, Дудь, Петров, Деревянко, Леонардо Ди Каприо
- Фильмы: Голливуд, Фиксики, Гринч, Бременские музыканты, пармезан, сыроварня

ОТВЕТ: только исправленный текст, без комментариев."""


def correct_text(original: str, max_retries: int = 3) -> str:
    url = config['baseUrl'] + '/chat/completions'
    body = json.dumps({
        "messages": [
            {"role": "assistant", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Исправь расшифровку:\n\n{original}"},
        ],
        "thinking": {"type": "disabled"},
    }).encode()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config["apiKey"]}',
        'X-Z-AI-From': 'Z',
        'X-Token': config.get('token', ''),
        'X-Chat-Id': config.get('chatId', ''),
        'X-User-Id': config.get('userId', ''),
    }

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (attempt + 1)
                print(f"  ⏳ 429, жду {wait}с")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            time.sleep(2 ** attempt)
            continue
    return original


for i in range(start, end):
    m = manifest[i]
    stem = Path(m["audio_path"]).stem
    out_path = OUT_DIR / f"{stem}.txt"

    if out_path.exists() and out_path.stat().st_size > 5:
        continue

    original = m.get("text", "")
    if not original:
        continue

    corrected = correct_text(original)
    if corrected:
        (OUT_DIR / f"{stem}.txt").write_text(corrected, encoding="utf-8")
        m["text_llm"] = corrected
        print(f"  [{i}] {stem[:50]}")
        print(f"    OLD: {original[:80]}")
        print(f"    NEW: {corrected[:80]}")

    time.sleep(2)

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n✅ Готово: {len(list(OUT_DIR.glob('*.txt')))} сегментов")
