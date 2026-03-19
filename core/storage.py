import os
from typing import Dict
from .models import VocabItem

WRONG_FILE = "wrong.txt"


def load_error_counts() -> Dict[tuple, int]:
    """
    Session-state loader.
    If wrong.txt is empty or missing => {}.
    Format: fi;en;count
    """
    errors: Dict[tuple, int] = {}

    if not os.path.exists(WRONG_FILE):
        return errors

    with open(WRONG_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(";")]
            if len(parts) < 3:
                continue

            fi = parts[0]
            en = parts[1]
            count_raw = parts[-1]
            try:
                count = int(count_raw)
            except ValueError:
                continue

            if count > 0:
                errors[(fi, en)] = count

    return errors


def save_error_counts(vocab: list[VocabItem]):
    """
    Session-state saver:
    Writes only items with error_count > 0 (remaining debt).
    Overwrites wrong.txt atomically each time.
    """
    temp_file = WRONG_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        for item in vocab:
            if item.error_count > 0:
                f.write(f"{item.fi};{item.en};{item.error_count}\n")

    os.replace(temp_file, WRONG_FILE)