# 🎙️ Датасет голоса Сергея Бурунова v2 (только Бурунов)

**77.7 минут чистого голоса Сергея Бурунова** — без ведущей, после pitch-фильтрации.

## 📊 Статистика

| Параметр | Значение |
|---|---|
| **Длительность** | 77.7 мин (4662 сек) |
| **Сегментов** | 602 |
| **Спикер** | Только Бурунов (M, pitch < 165 Hz) |

## 📁 Структура

```
burunov-only-v2/
├── segments/                     ← 602 WAV (только Бурунов)
├── transcripts_zai_asr/          ← 49 TXT (Z.AI ASR — лучшее качество)
├── transcripts_llm/              ← 75 TXT (LLM-коррекция — хорошее качество)
├── transcripts_whisper/          ← 602 TXT (Whisper tiny — базовое качество)
├── burunov-best.txt              ← лучший текст для каждого сегмента
├── manifest.json                 ← метаданные + speaker + pitch
├── asr_single.py                 ← скрипт Z.AI ASR
├── llm_correct_v2.py             ← скрипт LLM-коррекции
└── README.md
```

## 🎯 Три уровня качества

### Уровень 1: Whisper tiny (602/602) — `transcripts_whisper/`
Базовая расшифровка, ~70% точности. Галлюцинирует на разговорной речи.

### Уровень 2: LLM-коррекция (75/602) — `transcripts_llm/`
GLM-4 исправляет Whisper-текст: пунктуация, имена, осмысленные фразы.

### Уровень 3: Z.AI ASR (49/602) — `transcripts_zai_asr/` ⭐
Лучшее качество. GLM-4 based speech-to-text напрямую из аудио.

## 🚀 Как дослушать оставшиеся

### Z.AI ASR (лучшее качество, но rate-limited)
```bash
# Установить .z-ai-config или env vars
python asr_single.py  # делает 1 сегмент за запуск
# В цикле:
for i in $(seq 0 1 601); do python asr_single.py; sleep 5; done
```

### LLM-коррекция (быстрее, без rate limit)
```bash
python llm_correct_v2.py 0 1  # сегмент 0
python llm_correct_v2.py 1 1  # сегмент 1
# В цикле:
for i in $(seq 0 1 601); do python llm_correct_v2.py $i 1; sleep 2; done
```

## 📋 Формат manifest.json

```json
{
  "audio_path": "segments/xxx.wav",
  "duration": 8.45,
  "speaker": "M",
  "pitch_median": 87.5,
  "text": "Whisper tiny текст",
  "text_zai": "Z.AI ASR текст (если есть)",
  "text_llm": "LLM-коррекция (если есть)"
}
```
