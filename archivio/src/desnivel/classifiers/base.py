"""Interfaccia `EventClassifier`: arricchimenti incrementali del payload.

Un classifier osserva un evento gia' rilevato e il `Track` di provenienza,
e restituisce un piccolo dict che viene **fuso** nel payload dell'evento
dalla pipeline. Convenzione: il campo ``variants`` e' una lista di
etichette stringa, e piu' classifier possono contribuire (l'unione viene
fatta dalla pipeline).

Vantaggio architetturale: aggiungere una nuova variante (es. ``sunset``,
``urban``, ``coastal``) non richiede modifiche al contratto OSC ne' a
detector esistenti. Un nuovo classifier, un nuovo file, niente altro.

Vedi CONTRATTO-MODULAZIONI.md §3.1.1 e IMPLEMENTAZIONE.md §2.5.
"""
from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from ..events import Event
from ..track import Track


@runtime_checkable
class EventClassifier(Protocol):
    """Arricchisce il payload di un evento gia' rilevato.

    Attributes:
        applies_to_kinds: tupla di `kind` di eventi che il classifier
            esamina. Se ``None``, il classifier viene chiamato su tutti
            gli eventi.
    """

    applies_to_kinds: tuple[str, ...] | None

    def classify(self, event: Event, track: Track) -> Mapping[str, Any]:
        """Ritorna un dict da fondere nel payload dell'evento.

        Convenzioni:
        - dict vuoto: nessuna modifica (l'evento non e' pertinente).
        - chiave ``variants``: lista di stringhe; la pipeline fa l'unione
          con eventuali varianti gia' presenti, preservando l'ordine.
        - altre chiavi: aggiungono campi al payload (i conflitti con
          chiavi esistenti vengono sovrascritti dall'ultimo classifier).
        """
        ...
