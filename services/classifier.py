import json
import logging
from datetime import datetime, timezone
from typing import Any

import anthropic

from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None
MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """\
Você é um assistente que analisa mensagens de uma comunidade Discord de um produto de software.
Sua função é classificar cada mensagem e retornar um JSON estruturado.

Retorne APENAS um JSON válido, sem texto adicional, com exatamente estes campos:
{
  "category": "<bug|question|feedback|praise|off_topic|unknown>",
  "urgency": "<low|medium|high|critical>",
  "sentiment": "<positive|neutral|negative|frustrated>",
  "summary": "<resumo em 1-2 frases em português>",
  "tags": ["<tag1>", "<tag2>"],
  "confidence": <0.0 a 1.0>
}

Definições de categoria:
- bug: relato de erro, falha, comportamento inesperado do produto
- question: dúvida, pedido de ajuda, como fazer algo
- feedback: sugestão de melhoria, opinião sobre o produto
- praise: elogio, agradecimento
- off_topic: conversa não relacionada ao produto
- unknown: não é possível classificar com confiança

Definições de urgência:
- critical: sistema inacessível, perda de dados, bloqueio total de uso
- high: funcionalidade importante quebrada, bug afetando trabalho
- medium: problema que tem workaround, dúvida importante
- low: curiosidade, sugestão, elogio, off_topic
"""


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def _is_too_short(content: str) -> bool:
    words = [w for w in content.strip().split() if w.isalpha()]
    return len(words) < 5


async def analyze(
    content: str,
    channel_name: str,
    recent_context: list[str] | None = None,
) -> dict[str, Any]:
    if _is_too_short(content):
        return {
            "status": "done",
            "category": "unknown",
            "urgency": "low",
            "sentiment": "neutral",
            "summary": "Mensagem muito curta para classificar.",
            "tags": [],
            "confidence": 1.0,
            "classified_at": datetime.now(timezone.utc),
            "model_used": "rule_based",
        }

    context_block = ""
    if recent_context:
        context_block = "\n\nContexto recente do canal (últimas mensagens):\n" + "\n".join(
            f"- {m}" for m in recent_context[-4:]
        )

    user_message = (
        f"Canal: #{channel_name}{context_block}\n\n"
        f"Mensagem para classificar:\n{content}"
    )

    try:
        client = _get_client()
        response = await client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )

        raw = response.content[0].text.strip()
        data = json.loads(raw)

        return {
            "status": "done",
            "category": data.get("category", "unknown"),
            "urgency": data.get("urgency", "low"),
            "sentiment": data.get("sentiment", "neutral"),
            "summary": data.get("summary", ""),
            "tags": data.get("tags", []),
            "confidence": float(data.get("confidence", 0.0)),
            "classified_at": datetime.now(timezone.utc),
            "model_used": MODEL,
        }

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Falha ao parsear resposta do classificador: %s", e)
        return _fallback_classification()
    except anthropic.APIError as e:
        logger.error("Erro na API Anthropic: %s", e)
        return _fallback_classification()


def _fallback_classification() -> dict[str, Any]:
    return {
        "status": "error",
        "category": "unknown",
        "urgency": "low",
        "sentiment": "neutral",
        "summary": "Erro ao classificar.",
        "tags": [],
        "confidence": 0.0,
        "classified_at": datetime.now(timezone.utc),
        "model_used": MODEL,
    }
