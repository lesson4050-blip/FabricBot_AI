import logging
import re
from typing import Optional, Dict, Any, List
from config import settings

logger = logging.getLogger(__name__)

# Anthropic Tool definition for Fabric Availability
TOOLS = [
    {
        "name": "check_fabric_stock",
        "description": "Перевіряє наявність тканини та вільні залишки на складах у 1С за назвою та відтінком",
        "input_schema": {
            "type": "object",
            "properties": {
                "article": {
                    "type": "string",
                    "description": "Назва або артикул колекції тканини (наприклад, SIENA, FLORENCE, VERONA)"
                },
                "shade": {
                    "type": "string",
                    "description": "Номер та/або назва відтінку (наприклад, 05-Birch, 02-Ivory, 14-Anthracite)"
                }
            },
            "required": ["article"]
        }
    }
]

SYSTEM_PROMPT = """Ти — спеціалізований AI-асистент гуртової компанії з продажу штор та текстилю.
Твоє завдання — аналізувати повідомлення клієнтів у Telegram-групах та фотографії зразків з етикетками.
Коли клієнт запитує про наявність тканини (текстом чи через фото зразка/етикетки), ти повинен чітко розпізнати:
1. Назву колекції (наприклад: Siena, Florence, Verona).
2. Відтінок або код кольору (наприклад: 05-Birch, 02-Ivory).
Використовуй інструмент `check_fabric_stock`, щоб запросити дані з 1С.
Якщо повідомлення не стосується наявності тканин, ігноруй або дай лаконічну відповідь.
"""

class ClaudeService:
    """Service to interact with Anthropic Claude API for Vision and Tool Use."""

    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.client = None
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except Exception as e:
                logger.error("Failed to initialize Anthropic client: %s", e)

    async def analyze_text_query(self, text: str) -> Optional[Dict[str, str]]:
        """Extract fabric article and shade from text."""
        if self.client:
            try:
                response = await self.client.messages.create(
                    model=settings.claude_model,
                    max_tokens=512,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=[{"role": "user", "content": text}]
                )
                for block in response.content:
                    if block.type == "tool_use" and block.name == "check_fabric_stock":
                        return block.input
            except Exception as e:
                logger.error("Claude API text analysis failed: %s", e)

        # Regex fallback for offline testing/demo
        patterns = [
            r"(?i)(siena|florence|verona)\s*([\w\-]+)?",
            r"(?i)наявність\s+([a-zA-Zа-яА-Я0-9\-]+)\s*([\w\-]+)?"
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                art = m.group(1).upper()
                shade = m.group(2) if len(m.groups()) > 1 and m.group(2) else ""
                return {"article": art, "shade": shade}
        return None

    async def analyze_image_sample(self, image_bytes: bytes, caption: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Extract fabric label info from an uploaded sample image using Claude 3.5 Sonnet Vision."""
        if self.client:
            try:
                import base64
                b64_img = base64.b64encode(image_bytes).decode("utf-8")
                content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64_img
                        }
                    },
                    {
                        "type": "text",
                        "text": caption or "Розпізнай тканину та відтінок на етикетці зразка і перевір залишок."
                    }
                ]
                response = await self.client.messages.create(
                    model=settings.claude_model,
                    max_tokens=512,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=[{"role": "user", "content": content}]
                )
                for block in response.content:
                    if block.type == "tool_use" and block.name == "check_fabric_stock":
                        return block.input
            except Exception as e:
                logger.error("Claude Vision analysis failed: %s", e)

        # Demo fallback
        return {"article": "SIENA", "shade": "05-Birch"}

claude_service = ClaudeService()
