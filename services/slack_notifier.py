import logging
from typing import Any

import urllib.request
import urllib.error
import json

from config import SLACK_WEBHOOK_URL

logger = logging.getLogger(__name__)

_URGENCY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

_CATEGORY_EMOJI = {
    "bug": "🐛",
    "question": "❓",
    "feedback": "💬",
    "praise": "🌟",
    "off_topic": "💤",
    "unknown": "❔",
}


def _post(payload: dict[str, Any]) -> None:
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL não configurado.")
        return
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except urllib.error.URLError as e:
        logger.error("Falha ao enviar para o Slack: %s", e)


def send_hourly_digest(
    new_messages: int,
    unanswered_total: int,
    by_category: dict[str, int],
    by_urgency: dict[str, int],
    top_unanswered: list[dict[str, Any]],
) -> None:
    if not new_messages and not unanswered_total:
        return

    category_lines = " · ".join(
        f"{_CATEGORY_EMOJI.get(k, '')} {k}: *{v}*"
        for k, v in sorted(by_category.items(), key=lambda x: -x[1])
        if v > 0
    )
    urgency_lines = " · ".join(
        f"{_URGENCY_EMOJI.get(k, '')} {k}: *{v}*"
        for k, v in [("critical", by_urgency.get("critical", 0)),
                     ("high", by_urgency.get("high", 0)),
                     ("medium", by_urgency.get("medium", 0)),
                     ("low", by_urgency.get("low", 0))]
        if v > 0
    )

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📊 Resumo da última hora — Abacabot"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Novas mensagens*\n{new_messages}"},
                {"type": "mrkdwn", "text": f"*Sem resposta*\n{unanswered_total}"},
            ],
        },
    ]

    if category_lines:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Por categoria:*\n{category_lines}"},
        })

    if urgency_lines:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Por urgência:*\n{urgency_lines}"},
        })

    if top_unanswered:
        lines = []
        for msg in top_unanswered[:5]:
            urgency = msg.get("classification", {}).get("urgency", "low")
            summary = msg.get("classification", {}).get("summary") or msg.get("content", "")[:80]
            hours = msg.get("response_status", {}).get("hours_without_reply", 0)
            emoji = _URGENCY_EMOJI.get(urgency, "")
            lines.append(f"{emoji} _{summary}_ — sem resposta há *{hours:.0f}h*")

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Mensagens mais urgentes sem resposta:*\n" + "\n".join(lines),
            },
        })

    _post({"blocks": blocks})


def send_pattern_alert(
    category: str,
    tags: list[str],
    count: int,
    window_days: int,
) -> None:
    emoji = _CATEGORY_EMOJI.get(category, "❔")
    tags_str = ", ".join(f"`{t}`" for t in tags) if tags else "sem tags"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "⚠️ Alerta de padrão detectado"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Categoria*\n{emoji} {category}"},
                {"type": "mrkdwn", "text": f"*Relatos*\n{count} nos últimos {window_days} dias"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Tópicos em comum:* {tags_str}"},
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Verifique o Discord para investigar os relatos."}
            ],
        },
    ]

    _post({"blocks": blocks})
