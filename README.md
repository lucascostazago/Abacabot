# 🥑 Abacabot 

Bot de monitoramento para comunidades Discord. Lê, classifica e armazena mensagens automaticamente usando IA, ajudando times pequenos a acompanhar o que está acontecendo na comunidade sem precisar ficar de olho no chat o tempo todo.

---

## Como funciona

Toda mensagem enviada nos canais monitorados passa por três etapas:

```
Mensagem no Discord
       ↓
Salva no MongoDB (instantâneo)
       ↓
Claude AI classifica em background
       ↓
Documento atualizado com categoria, urgência e resumo
```

A cada 30 minutos, um scanner verifica mensagens sem resposta e escalona as que passaram do limite de horas configurado.

---

## Classificação

Cada mensagem recebe automaticamente:

| Campo | Valores possíveis |
|---|---|
| **Categoria** | `bug` · `question` · `feedback` · `praise` · `off_topic` · `unknown` |
| **Urgência** | `low` · `medium` · `high` · `critical` |
| **Sentimento** | `positive` · `neutral` · `negative` · `frustrated` |
| **Resumo** | Frase gerada pelo Claude descrevendo a mensagem |
| **Tags** | Tópicos detectados, ex: `["login", "pagamento"]` |

---

## Stack

- **Python 3.12**
- **discord.py** — eventos em tempo real
- **MongoDB** + **Motor** — armazenamento async
- **Claude API (Anthropic)** — classificação inteligente com prompt caching

---

## Estrutura

```
Abacabot/
├── bot/
│   ├── client.py                 # CommunityBot
│   ├── events/
│   │   ├── on_message.py         # captura e classifica mensagens
│   │   └── on_reaction.py        # reação ✅ do staff marca como respondida
│   └── tasks/
│       └── unanswered_scanner.py # job a cada 30min
├── services/
│   ├── classifier.py             # integração Claude API
│   └── message_store.py          # leitura/escrita MongoDB
├── db/
│   └── client.py                 # conexão Motor + índices
├── config.py
├── main.py
├── Dockerfile
└── docker-compose.yml
```

---

## Configuração

Copie o arquivo de exemplo e preencha as variáveis:

```bash
cp .env.example .env
```

| Variável | Descrição |
|---|---|
| `DISCORD_TOKEN` | Token do bot (Discord Developer Portal → Bot) |
| `MONGODB_URI` | URI de conexão do MongoDB |
| `ANTHROPIC_API_KEY` | Chave da API do Claude |
| `GUILD_ID` | ID do servidor Discord |
| `MONITORED_CHANNEL_IDS` | IDs dos canais separados por vírgula |
| `UNANSWERED_THRESHOLD_HOURS` | Horas até considerar mensagem sem resposta (padrão: 24) |

---

## Rodando localmente

```bash
docker compose up
```

Isso sobe o bot e um MongoDB local automaticamente.

---

## Marcando mensagens como respondidas

Qualquer membro com role `Time da Abacatepay"` ou `admin` pode reagir com ✅ em uma mensagem para marcá-la como respondida no banco.

---
