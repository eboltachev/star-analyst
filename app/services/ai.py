from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class OCRResult:
    text: str
    entities: dict


class VisionProvider:
    def extract(self, file_path: str) -> OCRResult:
        text = open(file_path, "r", encoding="utf-8", errors="ignore").read() if file_path.endswith(".txt") else "Скан документа: Иванов Иван Иванович ИНН 123456789012"
        entities = {
            "full_names": re.findall(r"[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+", text),
            "inn": re.findall(r"\b\d{10,12}\b", text),
            "dates": re.findall(r"\b\d{2}\.\d{2}\.\d{4}\b", text),
            "documents": re.findall(r"\b\d{2}\s?\d{2}\s?\d{6}\b", text),
        }
        return OCRResult(text=text, entities=entities)


class EmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        seed = float(len(text) % 10)
        return [seed] * 8


class LLMProvider:
    def build_report(self, context: dict) -> str:
        lines = [
            "# Аналитическая справка",
            "## Краткое резюме",
            f"Проверка по {context['request']['full_name']} завершена.",
            "## Ключевые факты",
        ]
        for ev in context["evidence"]:
            lines.append(f"- {ev['title']} (evidence:{ev['id']})")
        lines.extend([
            "## Ограничения",
            "Использованы только открытые источники и загруженные пользователем файлы.",
        ])
        return "\n".join(lines)

    def chat(self, question: str, context_chunks: list[str]) -> str:
        if not context_chunks:
            return "Недостаточно данных для подтверждённого ответа."
        return f"Ответ основан на evidence: {', '.join(context_chunks[:3])}. Вопрос: {question}"
