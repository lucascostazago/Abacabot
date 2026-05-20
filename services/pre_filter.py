import re

_QUESTION_PATTERNS = [
    r"\?",
    r"\bcomo\b", r"\bonde\b", r"\bquando\b", r"\bpor que\b", r"\bporque\b",
    r"\bpor quê\b", r"\bqual\b", r"\bquais\b", r"\bquem\b", r"\bpode\b",
    r"\bconsigo\b", r"\bdá pra\b", r"\bdá para\b", r"\btem como\b",
    r"\bé possível\b", r"\bcomo faço\b", r"\bcomo usar\b", r"\bcomo funciona\b",
    r"\bnão consigo\b", r"\bnao consigo\b", r"\bnão funciona\b", r"\bnao funciona\b",
    r"\bnão sei\b", r"\bnao sei\b", r"\bnão entendo\b", r"\bnao entendo\b",
    r"\bnão aparece\b", r"\bnao aparece\b", r"\bnão abre\b", r"\bnao abre\b",
    r"\bnão carrega\b", r"\bnao carrega\b", r"\bnão deixa\b", r"\bnao deixa\b",
    r"\bme ajuda\b", r"\bme ajude\b", r"\bpreciso de ajuda\b", r"\bajuda\b",
    r"\bsuporte\b", r"\bdúvida\b", r"\bduvida\b", r"\bpergunta\b",
]

_BUG_PATTERNS = [
    r"\berro\b", r"\berror\b", r"\bbug\b", r"\bfalha\b", r"\bproblema\b",
    r"\bquebrando\b", r"\bquebrado\b", r"\btravando\b", r"\btravou\b",
    r"\bcaindo\b", r"\bcaiu\b", r"\bnão abre\b", r"\bnao abre\b",
    r"\bnão funciona\b", r"\bnao funciona\b", r"\boutage\b", r"\bfora do ar\b",
    r"\binstabilidade\b", r"\blento\b", r"\btimeout\b", r"\b500\b", r"\b403\b",
    r"\b404\b", r"\bnão carrega\b", r"\bnao carrega\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _QUESTION_PATTERNS + _BUG_PATTERNS]


def is_relevant(content: str) -> bool:
    """Retorna True se a mensagem provavelmente é uma dúvida ou bug."""
    if len(content.strip().split()) < 5:
        return False
    return any(pattern.search(content) for pattern in _COMPILED)
