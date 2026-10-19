"""Sviluppo riproducibile di un motivo su più finestre musicali."""
import math
import random

from desnivel.music.phrases import Note, Phrase


def develop(degrees, intervals, root, request, values, origin):
    """Compone l'intero periodo per mantenere continuità fra richieste indipendenti.

    Il motivo guida le altezze; profilo, ritmo e chiusura dipendono dalla
    posizione nel periodo. Il risultato selezionato è una sola finestra.
    """
    length, windows = request.length_beats, values['phrase_windows']
    window_index = round((request.start-origin) / length)
    cycle, selected = divmod(window_index, windows)
    rng = random.Random(values['seed'] + cycle * 104729 + request.context.section_index * 1009)
    amount, activity, step = values['development'], values['activity'], values['step_beats']
    upper = max(max(degrees), len(intervals))
    pitches = {d: root+intervals[d % len(intervals)]+12*(d//len(intervals))
               for d in range(upper+1)}
    pitches = {d: p for d,p in pitches.items() if 0 <= p <= 127}
    if not pitches:
        raise ValueError('registro melodico fuori dal MIDI')
    previous, previous_move = degrees[0], 0
    chosen, descriptions = None, None
    for part in range(windows):
        fraction = part / (windows-1)
        if part == 0:
            phase = 'statement'
        elif part == windows-1:
            phase = 'resolution'
        elif fraction <= .5:
            phase = 'development'
        else:
            phase = 'contrast'
        cadence = phase == 'resolution'
        cadence_at = max(0., length-min(length*.4, step*1.5)) if cadence else length
        notes, beat, attacks = [], 0., 0
        while beat < cadence_at-1e-9:
            if attacks >= 128:
                raise ValueError('lo sviluppo supera 128 eventi per finestra')
            # Il passo è un riferimento, non un obbligo di note equidistanti.
            durations = [.5, 1., 1.5, 2.]
            weights = [activity*amount*(1.4 if phase=='development' else .7),
                       1., .35*amount, (1-activity)*1.2+.1]
            slot = min(rng.choices(durations, weights=weights)[0]*step, cadence_at-beat)
            anchor = phase == 'statement' and attacks < min(3, len(degrees))
            motif_index = int((part*length+beat)/step) % len(degrees)
            if phase == 'contrast':
                motif_index = (len(degrees)-1-motif_index) % len(degrees)
            target = degrees[attacks] if anchor and attacks < len(degrees) else degrees[motif_index]
            if phase == 'development':
                target = min(upper, target+max(1, round(amount*2)))
            if cadence:
                target = round(target*(1-beat/max(cadence_at, 1e-9)))
            rest = attacks > 0 and not anchor and rng.random() < (1-activity)*amount*.45
            if not rest:
                if anchor:
                    degree = target
                else:
                    # Arco moderato; i salti sono limitati a una quinta e, dopo
                    # un salto ampio, è favorita una risposta per grado opposto.
                    center = min(upper, max(degrees)*.5 + math.sin(math.pi*fraction)*len(intervals)*.45)
                    candidates, scores = [], []
                    for d, pitch in pitches.items():
                        if abs(pitch-pitches[previous]) > 7:
                            continue
                        move = d-previous
                        recovery = max(0, move*previous_move) if abs(previous_move)>2 else 0
                        score = (-abs(d-target)*1.15 - abs(move)*.2
                                 -abs(d-center)*.45*amount - (1.1 if move==0 else 0)
                                 -recovery*.5)
                        candidates.append(d)
                        scores.append(score)
                    top = max(scores)
                    weights = [math.exp((score-top)/(.3+amount*.7)) for score in scores]
                    degree = rng.choices(candidates, weights=weights)[0]
                pitch = pitches[degree]
                accent = 5 if beat == 0 else (-7 if beat % 1 else 0)
                velocity = max(1, min(127, round(values['velocity']+accent+rng.uniform(-3,3)*amount)))
                duration = slot*min(1., values['articulation']*rng.uniform(.9,1.05))
                notes.append(Note(beat, pitch, duration, velocity))
                previous_move, previous = degree-previous, degree
            beat += slot
            attacks += 1
        if cadence:
            # Conclude sulla tonica: nel registro di base quando vicina,
            # altrimenti nell'ottava più prossima all'ultima nota.
            last_pitch = notes[-1].pitch if notes else root
            tonics = [root+12*k for k in range(11) if 0 <= root+12*k <= 127]
            tonic = root if abs(last_pitch-root) <= 7 else min(tonics, key=lambda p: (abs(p-last_pitch),p))
            hold = (length-cadence_at)*.9
            notes.append(Note(cadence_at, tonic, hold, max(1, values['velocity']-5)))
            previous_move, previous = -previous, 0
        if part == selected:
            chosen = Phrase(length, tuple(notes))
            descriptions = {
                'method': 'motif_development', 'phase': phase,
                'cycle': cycle, 'window': selected+1, 'windows': windows,
                'seed': values['seed'],
                'summary': f"{dict(statement='presentazione', development='sviluppo', contrast='contrasto', resolution='conclusione')[phase]} · finestra {selected+1}/{windows} · ciclo {cycle+1}",
            }
    return chosen, descriptions
