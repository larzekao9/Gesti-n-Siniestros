"""Rate limiter compartido (slowapi).

Vive en su propio módulo para que tanto `main.py` (que registra el handler de
`RateLimitExceeded`) como los routers que aplican `@limiter.limit(...)` usen la
MISMA instancia sin imports circulares (main importa routers, los routers no
pueden importar de main). DT-10.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
"""Limita por IP del cliente. Se aplica a endpoints sensibles de auth."""
