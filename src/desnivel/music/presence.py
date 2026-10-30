"""Partecipazione di una voce per una frase intera, indipendente dalle note."""
from hashlib import blake2b


def participates(voice: str, start: float, presence: float) -> bool:
    """Soglia riproducibile per voce e inizio frase; 0 e 1 sono esatti."""
    if presence <= 0:
        return False
    if presence >= 1:
        return True
    key = f'{voice}:{float(start).hex()}'.encode('utf-8')
    threshold = int.from_bytes(blake2b(key, digest_size=8).digest(), 'big') / 2**64
    return threshold < presence
