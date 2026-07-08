#!/usr/bin/env python3
"""
Z.AI ASR с большими паузами (5 сек) для избежания rate limit.
Делает по 1 сегменту за вызов.
"""

import json
import base64
import urllib.request
import time
import sys
from pathlib import Path

MANIFEST = Path("/home/z/burunov-v2/manifest.json")
SEG_DIR = Path("/home/z/burunov-v2/segments")
OUT_DIR = Path("/home/z/burunov-v2/transcripts_zai")

config = json.loads(open('/etc/.z-ai-config').read())

with open(MANIFEST) as f:
    manifest = json.load(f)

# Найти первый несделанный сегмент
todo_idx = None
for i, m in enumerate(manifest):
    stem = Path(m["audio_path"]).stem
    out_path = OUT_DIR / f"{stem}.txt"
    if not out_path.exists():
        todo_idx = i
        break

if todo_idx is None:
    print("✅ Всё готово!")
    sys.exit(0)

item = manifest[todo_idx]
stem = Path(item["audio_path"]).stem
wav_path = SEG_DIR / f"{stem}.wav"

print(f"📊 Сегмент {todo_idx}: {stem}")

# Пауза перед запросом
time.sleep(3)

with open(wav_path, 'rb') as f:
    audio_b64 = base64.b64encode(f.read()).decode()

url = config['baseUrl'] + '/audio/asr'
body = json.dumps({'file_base64': audio_b64}).encode()
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {config["apiKey"]}',
    'X-Z-AI-From': 'Z',
    'X-Token': config.get('token', ''),
    'X-Chat-Id': config.get('chatId', ''),
    'X-User-Id': config.get('userId', ''),
}

try:
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        text = result.get("text", "").strip()
        if text:
            (OUT_DIR / f"{stem}.txt").write_text(text, encoding="utf-8")
            item["text_zai"] = text
            with open(MANIFEST, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            print(f"✅ {text[:100]}")
        else:
            print(f"⚠️ Пустой ответ")
except Exception as e:
    print(f"❌ {e}")
