# ==========================================
# LIMITE DE TENTATIVAS DE SENHA
# ==========================================
# Depois de muitas senhas erradas seguidas, bloqueia novas tentativas por um
# tempo. Protege o login e a senha do Painel dos Adultos contra adivinhação.
# Fica em memória: basta para um servidor só (como no Docker do projeto).

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException

MAX_FAILURES = 8          # erros permitidos...
WINDOW_SECONDS = 5 * 60   # ...dentro de 5 minutos

_failures = defaultdict(deque)
_lock = Lock()


def _recent(key: str, now: float) -> deque:
    attempts = _failures[key]
    while attempts and now - attempts[0] > WINDOW_SECONDS:
        attempts.popleft()
    return attempts


def check(*keys: str) -> None:
    """Recusa com 429 se alguma das chaves (usuário, IP) errou demais há pouco."""
    now = time.monotonic()
    with _lock:
        for key in keys:
            attempts = _recent(key, now)
            if len(attempts) >= MAX_FAILURES:
                wait = int(WINDOW_SECONDS - (now - attempts[0])) // 60 + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Muitas tentativas com senha errada. Tente de novo em {wait} min.",
                )


def failed(*keys: str) -> None:
    now = time.monotonic()
    with _lock:
        for key in keys:
            _recent(key, now).append(now)


def succeeded(*keys: str) -> None:
    with _lock:
        for key in keys:
            _failures.pop(key, None)


def reset() -> None:
    with _lock:
        _failures.clear()
