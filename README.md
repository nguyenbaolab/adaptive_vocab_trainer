# Adaptive Vocabulary Trainer

An intelligent desktop vocabulary trainer (Finnish <-> English) built with `PySide6`.
The app focuses on reviewing mistakes within each session so you retain words longer instead of memorizing in a fixed order.

## Key Features

- Clean and simple desktop workflow (Setup -> Quiz -> Summary).
- Supports multiple `.txt` vocabulary files in one session.
- Three question types:
  - Finnish -> English (Multiple Choice)
  - English -> Finnish (Multiple Choice)
  - English -> Finnish (Typing)
- Adaptive mistake handling:
  - Wrong answers create "debt" (extra reviews required).
  - Missed words reappear with spacing and probability-based interleaving.
- `Hardcore Mode`:
  - Each word must pass both MC and Typing requirements.
  - Stricter mode designed for stronger retention.
- Session summary dashboard:
  - Correct/Wrong totals, accuracy, and study time.
  - Performance by question type.
  - Most-missed words in the current session.
- Session debt state is stored in `wrong.txt`.

## Tech Stack

- Python
- PySide6 (Qt for Python)

## Project Structure

```text
adaptive_vocab_trainer/
├─ app.py
├─ wrong.txt
├─ core/
│  ├─ models.py
│  ├─ loader.py
│  ├─ storage.py
│  ├─ session_stats.py
│  ├─ engine.py
│  └─ hardcore_engine.py
└─ ui/
   ├─ setup_screen.py
   ├─ quiz_screen.py
   └─ summary_screen.py
```

## Installation

Requirements:
- Python 3.10+ (you may be using 3.14)

Install dependency:

```bash
pip install PySide6
```

If `pip` points to a different Python version:

```bash
python -m pip install PySide6
```

On your current machine, you can also use:

```powershell
C:\Users\ADMIN\AppData\Local\Programs\Python\Python314\python.exe -m pip install PySide6
```

## Run the App

From the project folder:

```bash
python app.py
```

## Vocabulary File Format

Each line in a `.txt` file should follow:

```text
finnish;english
```

Example:

```text
koira;dog
kissa;cat
kirja;book
talo;house
```

Notes:
- Every line must contain a `;`.
- You need at least 4 total words to generate multiple-choice questions.
- For typing mode, you can define multiple accepted Finnish answers with `|`:
  - Example: `hei|moi;hi`

## How to Use

1. Click **Browse Vocabulary Files** and select one or more `.txt` files.
2. Choose the question types you want.
3. Set session size (app validates 5-200).
4. (Optional) Enable **Hardcore Mode**.
5. Click **Start Session**.
6. Complete the quiz -> review summary -> restart or return to setup.

## Adaptive Learning Logic (Quick Overview)

### Normal Mode
- The session starts with a random pool of words.
- Wrong answers add debt and trigger spaced/probabilistic reviews.
- After all new words are introduced, the engine switches to debt-only until all debt is cleared.

### Hardcore Mode
- Each word gets two first-pass tasks: 1 MC + 1 Typing.
- Debt is only cleared reliably after demonstrating mastery across both MC and Typing.
- Goal: stronger recall and less guessing-based success.

## What is `wrong.txt`?

- This file stores remaining debt in the format:

```text
finnish;english;count
```

- The app overwrites this file during session progress.
- It represents current session review state, not long-term learning history.

## Roadmap Ideas

- Package as a Windows `.exe`.
- Add CSV/Anki import.
- Add user profiles and multi-session analytics.
- Add date-based spaced repetition.

## Contributing

Pull requests and issues are welcome.
If you want, next I can also add:
- a proper Python/PySide `.gitignore`
- a Windows `.exe` build script
- sample vocabulary data for quick demo