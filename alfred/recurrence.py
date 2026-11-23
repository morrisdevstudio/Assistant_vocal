"""Calcul d'occurrences hebdomadaires à l'heure civile de Paris."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")


def next_weekly(anchor: datetime, after: datetime) -> datetime:
    """Prochaine occurrence strictement future, avec heure locale conservée.

    En cas d'heure inexistante au printemps, avancer à la première minute valide ;
    à l'automne, choisir la première occurrence de l'heure répétée.
    """
    local_anchor = anchor.astimezone(PARIS)
    now = after.astimezone(PARIS)
    candidate_date = now.date() + timedelta(days=(local_anchor.weekday() - now.weekday()) % 7)
    while True:
        wall = datetime.combine(candidate_date, local_anchor.timetz().replace(tzinfo=None))
        for _ in range(181):
            candidate = wall.replace(tzinfo=PARIS, fold=0)
            if candidate.astimezone(timezone.utc).astimezone(PARIS).replace(tzinfo=None) == wall:
                break
            wall += timedelta(minutes=1)
        else:
            raise ValueError("Impossible de résoudre l'heure locale du rappel.")
        if candidate.astimezone(timezone.utc) > after.astimezone(timezone.utc):
            return candidate.astimezone(timezone.utc)
        candidate_date += timedelta(days=7)
