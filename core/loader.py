import os
from typing import List
from .models import VocabItem


def load_vocab_files(file_paths: List[str]) -> List[VocabItem]:
    vocab = []

    for path in file_paths:
        if not os.path.isfile(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ";" not in line:
                    continue

                fi, en = line.split(";", 1)
                vocab.append(VocabItem(fi=fi.strip(), en=en.strip()))

    return vocab