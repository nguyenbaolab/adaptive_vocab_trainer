# Section 6 — Feature List

**App:** Finnish Vocabulary Quiz App  
**Version:** v1.0  
**Author:** Viet Bao Nguyen  
**Last updated:** 2026-03-26  
**Status:** Confirmed

---

## Format convention

Each feature follows this structure:

```
### F[X.Y] — Feature name
**Screen:** [screen name]  
**User story:** As a [user], I want [action] so that [outcome].  
**Business rules:** Numbered list of rules the implementation must respect.  
**Acceptance criteria:** Checkbox list — each item is a testable condition.  
```

---

## F1 — Setup Screen

---

### F1.1 — Topic selection

**Screen:** Setup  
**User story:** As a learner, I want to select one or more vocabulary topics so that I can focus my session on specific word groups.

**Business rules:**
1. At least 1 topic must be selected before the Start button becomes active.
2. Multiple topics can be selected simultaneously; words from all selected topics are merged into the session pool.
3. Each topic chip displays the number of words it contains (e.g. "Animals · 24").
4. Topics with 0 words are displayed in a disabled/greyed-out state with a tooltip: "No words in this topic yet."
5. Topic selection persists within the Setup screen until the user starts a session or navigates away.
6. If a selected topic is deleted from Vocab Management while Setup is open, it is automatically deselected.

**Acceptance criteria:**
- [ ] Topic chips render as a multi-select list; tapping toggles selected/unselected state.
- [ ] Selected topics are visually distinct (highlighted border or filled chip).
- [ ] Word count is displayed on each chip.
- [ ] Topics with 0 words cannot be selected; tapping them shows an explanation tooltip.
- [ ] Start button is disabled when no topic is selected.
- [ ] Selecting multiple topics merges their word pools correctly in the quiz engine.

---

### F1.2 — Word count picker

**Screen:** Setup  
**User story:** As a learner, I want to choose how many words to study per session so that I can control how long my session takes.

**Business rules:**
1. The word count represents the number of unique words in the initial session queue (before any debt words are added).
2. Default value is 20.
3. The maximum selectable value is capped at the total number of unique words across all selected topics. If no topics are selected yet, the picker shows the default of 20 but is non-blocking.
4. If the user selects a count higher than the available pool (e.g. due to topic deselection after setting the count), the count auto-adjusts down to the available pool size and shows a warning: "Only [N] words available in selected topics."
5. Minimum value is 5.
6. Preset quick-select options are provided (e.g. 10, 20, 30, 50) in addition to a manual input or slider.

**Acceptance criteria:**
- [ ] Default value is 20 on first load.
- [ ] Picker does not allow values below 5 or above the available word pool.
- [ ] Auto-cap triggers and shows a warning when the pool shrinks below the selected count.
- [ ] Preset options are tappable shortcuts; custom input is also supported.
- [ ] Word count selected is correctly passed to the quiz engine as the initial queue size.

---

### F1.3 — Question type selection

**Screen:** Setup  
**User story:** As a learner, I want to choose which question types are included in my session so that I can customise the style of practice.

**Business rules:**
1. There are 4 question types available:
   - **FI→EN MC:** A Finnish word is shown; user selects the English meaning from 4 options.
   - **EN→FI MC:** An English word is shown; user selects the Finnish word from 4 options.
   - **FI→EN Typing:** A Finnish word is shown; user types the English meaning.
   - **EN→FI Typing:** An English word is shown; user types the Finnish word.
2. At least 1 question type must be selected before the Start button becomes active.
3. Any combination of the 4 types is valid.
4. When Hardcore Mode is ON (F1.4), EN→FI Typing is force-enabled and its checkbox is locked (cannot be unticked). A tooltip explains: "EN→FI Typing is required in Hardcore Mode."
5. When Hardcore Mode is turned OFF, EN→FI Typing reverts to the state it was in before Hardcore was enabled (not reset to unchecked).
6. The selected types determine which question types appear in the quiz engine. The engine distributes questions across selected types with roughly equal probability, subject to the debt queue algorithm (F2.3).

**Acceptance criteria:**
- [ ] All 4 question type checkboxes are rendered and independently toggleable.
- [ ] Start button is disabled when no type is selected.
- [ ] When Hardcore Mode is ON, EN→FI Typing checkbox is checked and visually locked (disabled state with lock icon or tooltip).
- [ ] When Hardcore Mode is turned OFF, EN→FI Typing returns to its pre-Hardcore state.
- [ ] The quiz engine only generates questions of the selected types.
- [ ] Question type labels clearly communicate direction and format (e.g. "Finnish → English · Multiple choice").

---

### F1.4 — Hardcore mode toggle

**Screen:** Setup  
**User story:** As a learner, I want to enable Hardcore Mode so that every word must be answered correctly across all selected question types before it is considered cleared.

**Business rules:**
1. Hardcore Mode is an on/off toggle, off by default.
2. When Hardcore Mode is ON:
   - A word is only "cleared" (debt = 0 eligible) when it has been answered correctly in **every selected question type** at least once in the session.
   - EN→FI Typing is force-enabled in F1.3 and cannot be deselected.
   - Per-type correctness is tracked independently per word (e.g. a word can be correct in MC but still pending in Typing).
3. When Hardcore Mode is OFF:
   - A word is cleared when its debt reaches 0 through the standard debt algorithm (F2.3), regardless of question type.
4. The Hardcore Mode state persists across app sessions (stored in AsyncStorage).
5. A tooltip or explainer text is shown near the toggle to describe the mode: "Each word must pass all selected question types to be cleared."
6. Toggling Hardcore Mode mid-Setup (before starting) is allowed. Toggling mid-session is not supported in v1.

**Acceptance criteria:**
- [ ] Toggle is OFF by default on first install; persists across sessions after first interaction.
- [ ] When toggled ON, EN→FI Typing is force-checked in F1.3 and locked.
- [ ] When toggled OFF, EN→FI Typing reverts to its previous state.
- [ ] Tooltip or description text is visible near the toggle explaining Hardcore rules.
- [ ] In a Hardcore session, a word is not cleared until it has been answered correctly in every selected question type.
- [ ] Per-type correctness state is tracked and cleared independently per word.
- [ ] Hardcore state is persisted to AsyncStorage and restored on next app open.

---

## F2 — Quiz Screen

---

### F2.1 — Multiple choice question

**Screen:** Quiz  
**User story:** As a learner, I want to be shown a word and select the correct answer from 4 options so that I can test my passive recognition.

**Business rules:**
1. The question displays the source word prominently and clearly indicates the direction (e.g. "What does this mean in English?" or "Choose the Finnish word").
2. 4 answer options are always shown — 1 correct answer and 3 distractors.
3. Distractors are selected from the same topic(s) as the correct answer to maximise relevance and difficulty. If the topic does not have enough words, distractors are drawn from other selected topics.
4. If the total word pool has fewer than 4 words, the number of options equals the pool size (minimum 2). This edge case should display a warning at Setup if the pool is too small.
5. Answer options are shuffled randomly each time a question is rendered.
6. Tapping an option immediately locks all options (prevents double-tap) and shows feedback:
   - Correct: option highlights green; auto-advances after 800ms.
   - Wrong: selected option highlights red, correct option highlights green; auto-advances after 1200ms.
7. The question type label (e.g. "FI → EN · Multiple choice") is shown above the question card.

**Acceptance criteria:**
- [ ] Question card shows source word and direction label.
- [ ] Exactly 4 options are shown (or fewer if pool is too small).
- [ ] Distractors are drawn from same topic; fallback to other topics if needed.
- [ ] Options are shuffled on every render.
- [ ] Tapping locks all options immediately.
- [ ] Correct answer shows green highlight; wrong answer shows red on selected and green on correct.
- [ ] Auto-advances to next question after feedback delay.

---

### F2.2 — Typing question

**Screen:** Quiz  
**User story:** As a learner, I want to type the answer to a question so that I can practise active recall.

**Business rules:**
1. The question displays the source word and direction label (e.g. "EN → FI · Typing" or "FI → EN · Typing").
2. A text input field is shown. The user types their answer and submits via the Submit button or the Enter/Return key on the keyboard.
3. Answer evaluation is **case-insensitive** (e.g. "koira" = "Koira").
4. Leading and trailing whitespace is trimmed before evaluation.
5. **Accent leniency rule (FI→EN Typing only):** Since the target is English, strict matching is applied. No leniency needed.
6. **Accent leniency rule (EN→FI Typing):** By default, the app accepts answers where ä is substituted with a, and ö is substituted with o (lenient mode). This behaviour is configurable via a setting (see F8 — Accent leniency setting, if added; default = lenient in v1).
7. Submitting an empty input triggers a shake animation on the input field and does NOT count as an attempt (no debt penalty, no accuracy impact).
8. On wrong answer: the correct answer is shown below the input field in a "Correct answer: [word]" label. Auto-advances after 1500ms.
9. On correct answer: brief green highlight on the input field. Auto-advances after 800ms.
10. If the answer used a hint (F2.5), the question is marked as "assisted": correct but not counted toward debt reduction or accuracy percentage.

**Acceptance criteria:**
- [ ] Text input and Submit button are shown; Enter key also submits.
- [ ] Evaluation is case-insensitive and trims whitespace.
- [ ] Empty submission triggers shake animation, no penalty recorded.
- [ ] EN→FI Typing accepts a/o as substitutes for ä/ö by default.
- [ ] Wrong answer shows "Correct answer: [word]" and auto-advances after 1500ms.
- [ ] Correct answer shows green highlight and auto-advances after 800ms.
- [ ] Assisted answers (via hint) are marked separately and excluded from accuracy and debt calculations.

---

### F2.3 — Debt-based word queue

**Screen:** Quiz (engine logic)  
**User story:** As a learner, I want words I answered incorrectly to reappear more frequently so that I am forced to review my weak words until I master them.

**Business rules:**
1. Every word in the session has a `debtCount` integer, initialised to 0.
2. **Debt increment on wrong answer:**
   - 1st wrong answer for a word: `debtCount += 2`
   - 2nd wrong answer for the same word: `debtCount += 3`
   - 3rd and subsequent wrong answers: `debtCount += 2` per occurrence
   - Maximum `debtCount` per word is capped at **10**.
3. **Debt decrement on correct answer:** Each correct answer (non-assisted) reduces `debtCount` by 1.
4. A word with `debtCount > 0` is considered "in debt" and remains in the active queue.
5. A word with `debtCount = 0` after at least one correct answer is considered "cleared" and is removed from the queue.
   - Exception: In Hardcore Mode (F1.4), a word is only eligible for clearance when it has been answered correctly in **every selected question type** at least once, in addition to `debtCount = 0`.
6. **Probability-weighted selection:** Words with higher debt are more likely to be selected as the next question. The selection weight of a word is proportional to `debtCount + 1` (so even cleared-eligible words have a chance before removal).
7. **Minimum spacing rule:** A word cannot appear again until at least **3 other questions** have been asked since its last appearance, regardless of debt. This prevents the same word from appearing consecutively.
8. The session ends when all words have `debtCount = 0` and all words meet the Hardcore clearance condition (if applicable), OR when the user manually exits (F2.6).
9. The `debtCount` for each word is saved to persistent storage at session end (F5).

**Acceptance criteria:**
- [ ] `debtCount` initialises at 0 for every word at session start.
- [ ] First wrong answer increments debt by 2; second by 3; third and beyond by 2; capped at 10.
- [ ] Correct non-assisted answer decrements debt by 1.
- [ ] Words with debt > 0 remain in queue; words with debt = 0 (and Hardcore condition met) are removed.
- [ ] High-debt words appear more frequently than low-debt words.
- [ ] Same word does not appear within 3 questions of its previous appearance.
- [ ] Session ends only when all words are cleared.
- [ ] Debt state is persisted at session end.

---

### F2.4 — Hardcore mode interleaving

**Screen:** Quiz  
**User story:** As a learner in Hardcore Mode, I want question types to be interleaved randomly so that I cannot predict what type is coming next and must be prepared for any format.

**Business rules:**
1. This feature is only active when Hardcore Mode is ON (F1.4).
2. For each word in the session, the quiz engine tracks which of the selected question types have been answered correctly. This is stored as a per-word, per-type correctness map: `{ wordId: { 'fi_en_mc': false, 'en_fi_typing': true, ... } }`.
3. Question types for each word are served in **random order** across the session — not in a fixed sequence (e.g. not all MC first then all Typing). The engine interleaves question types across all words.
4. A word is only eligible for clearance when all of the following are true:
   - `debtCount = 0`
   - All selected question types for that word have been answered correctly at least once.
5. If a user answers a question type correctly for a word but later answers a different type incorrectly for the same word, the correct result for the first type is **retained** — per-type correctness is not reset by a wrong answer on a different type.
6. Debt still increments/decrements via the standard rules (F2.3) regardless of question type.
7. Wrong answer on any type triggers the debt penalty (F2.3) for that word.

**Acceptance criteria:**
- [ ] Per-word, per-type correctness map is initialised at session start when Hardcore is ON.
- [ ] Question types appear in random interleaved order across the session.
- [ ] A word is not cleared until debtCount = 0 AND all selected types have been answered correctly.
- [ ] Correct results for individual question types are retained even if the word accrues new debt on a different type.
- [ ] Debt increments/decrements apply normally regardless of question type.

---

### F2.5 — Hint / reveal in typing question

**Screen:** Quiz  
**User story:** As a learner, I want to request a hint when I am stuck on a typing question so that I can get unstuck without fully giving up.

**Business rules:**
1. A "Hint" button is shown on every Typing question (both FI→EN and EN→FI).
2. Each tap of the Hint button reveals **one additional character** of the correct answer in sequence (e.g. first tap: "k", second tap: "ko", third tap: "koi"...).
3. Tapping Hint does not count as a wrong answer and does not trigger debt increment.
4. Once Hint has been used (any number of times) on a question, that question instance is flagged as **"assisted"** for the remainder of the attempt.
5. Submitting a correct answer on an assisted question:
   - Does **not** reduce `debtCount`.
   - Does **not** count toward the accuracy percentage.
   - Is recorded as "assisted correct" in session stats.
   - In Hardcore Mode: does **not** satisfy the per-type correctness requirement — the user must answer without hint to mark that type as passed.
6. If the user submits a wrong answer even after using hints, normal debt penalty applies (the hint did not help — F2.3 rules).
7. The hint state resets when the question advances to the next word.

**Acceptance criteria:**
- [ ] Hint button is visible on all Typing questions.
- [ ] Each tap reveals one more character of the correct answer.
- [ ] Using hint does not trigger a debt penalty.
- [ ] Assisted flag is set on first hint tap.
- [ ] Correct assisted answer does not reduce debt and is excluded from accuracy %.
- [ ] In Hardcore Mode, an assisted correct answer does not satisfy the per-type clearance requirement.
- [ ] Wrong answer after hint use still triggers debt penalty.
- [ ] Hint state resets on question advance.

---

### F2.6 — Exit mid-session

**Screen:** Quiz  
**User story:** As a learner, I want to be able to stop a session early so that I am not forced to complete a full session if time runs out.

**Business rules:**
1. An Exit button is always visible during the quiz.
2. Tapping Exit shows a confirmation dialog: "End session? Your progress will be saved." with options "End session" and "Keep going".
3. If the user confirms exit:
   - The current debt state (all `debtCount` values) is saved to persistent storage (F5).
   - The session is marked as "incomplete" with the timestamp and partial stats.
   - The user is navigated to the Summary screen (F3) with an "Incomplete session" badge.
4. If the user cancels, the quiz resumes exactly where it left off with no state change.
5. The timer continues running while the confirmation dialog is shown (not paused).

**Acceptance criteria:**
- [ ] Exit button is always visible during quiz.
- [ ] Tapping Exit shows confirmation dialog with correct copy.
- [ ] Confirming saves debt state to persistent storage.
- [ ] Confirming navigates to Summary screen with "Incomplete session" badge.
- [ ] Cancelling dismisses dialog and resumes quiz with no state change.
- [ ] Timer is not paused while dialog is open.

---

## F3 — Summary Screen

---

### F3.1 — Session stats

**Screen:** Summary  
**User story:** As a learner, I want to see a breakdown of my session performance so that I can understand how well I did.

**Business rules:**
1. The following metrics are always displayed:
   - **Total correct:** number of non-assisted correct answers.
   - **Total wrong:** number of wrong answers (including debt re-attempts).
   - **Accuracy %:** `(correct / (correct + wrong)) * 100`, rounded to 1 decimal. Assisted correct answers are excluded from both numerator and denominator.
   - **Session time:** total elapsed time in mm:ss format.
2. A per-type breakdown is shown for each active question type, displaying correct and wrong counts separately for MC and Typing (and by direction if both FI→EN and EN→FI are used).
3. If the session was exited early (F2.6), an "Incomplete session" badge is shown next to the title.
4. Assisted correct answers are shown as a separate count: "X answered with hint" — informational only, does not affect accuracy.

**Acceptance criteria:**
- [ ] All 4 primary metrics (correct, wrong, accuracy, time) are displayed.
- [ ] Accuracy excludes assisted answers from calculation.
- [ ] Per-type breakdown is shown for each selected question type.
- [ ] "Incomplete session" badge appears when session was exited early.
- [ ] Assisted answer count is shown separately.

---

### F3.2 — Most-missed words (top 5)

**Screen:** Summary  
**User story:** As a learner, I want to see which words I struggled with most in this session so that I know where to focus my next review.

**Business rules:**
1. Displays the **top 5 words** with the highest total wrong answer count in the current session.
2. Each entry shows: Finnish word, English word, and number of times answered incorrectly in the session.
3. If fewer than 5 words were answered incorrectly, only the words with at least 1 wrong answer are shown.
4. If no words were answered incorrectly (perfect session), this section is hidden and a "Perfect session!" message is shown instead.
5. Words are ranked by wrong count descending. Ties are broken alphabetically by Finnish word.

**Acceptance criteria:**
- [ ] Up to 5 words shown, ranked by wrong count descending.
- [ ] Each entry shows FI word, EN word, and wrong count.
- [ ] Section is hidden on a perfect session; success message is shown instead.
- [ ] Tie-breaking is alphabetical by Finnish word.

---

### F3.3 — Remaining debt display

**Screen:** Summary  
**User story:** As a learner, I want to see which words still have outstanding debt after my session so that I know what will carry over to my next session.

**Business rules:**
1. Lists all words where `debtCount > 0` at session end.
2. Each entry shows: Finnish word, English word, and current `debtCount`.
3. Words are sorted by `debtCount` descending.
4. If `debtCount = 0` for all words (session fully completed), this section is hidden entirely.
5. In Hardcore Mode, words that have `debtCount = 0` but have not passed all question types are also listed here, with a label indicating which types remain: e.g. "Still needs: EN→FI Typing".

**Acceptance criteria:**
- [ ] All words with debtCount > 0 are listed, sorted descending.
- [ ] Each entry shows FI word, EN word, and debtCount.
- [ ] Section is hidden when no debt remains.
- [ ] In Hardcore Mode, words pending on a question type (even with debt = 0) are included with a type label.

---

### F3.4 — Review missed words

**Screen:** Summary  
**User story:** As a learner, I want to immediately drill the words I missed in this session so that I can reinforce them while they are fresh.

**Business rules:**
1. A "Review missed words" CTA button is shown on the Summary screen.
2. The button is disabled (greyed out) if there are no missed words in the current session (total wrong count = 0 and no remaining debt).
3. Tapping the button launches a **mini-session** using only the words that were answered incorrectly at least once in the previous session.
4. The mini-session uses the same Setup configuration (question types, Hardcore mode) as the original session. No Setup screen is shown — it launches directly.
5. In the mini-session, each word starts with `debtCount = 0` (fresh start for the drill, not carrying over the debt from the main session — the debt is already persisted in F5).
6. The mini-session follows all the same quiz engine rules (F2.1–F2.6), including debt accumulation if the user gets words wrong again.
7. After the mini-session ends, the user is returned to a new Summary screen reflecting the mini-session results.

**Acceptance criteria:**
- [ ] "Review missed words" button is visible on Summary screen.
- [ ] Button is disabled when there are no missed words.
- [ ] Tapping launches mini-session with only missed words in the queue.
- [ ] Mini-session uses same question types and Hardcore config as original session.
- [ ] Words start at debtCount = 0 in the mini-session.
- [ ] All quiz engine rules apply in the mini-session.
- [ ] Mini-session ends on its own Summary screen.

---

## F4 — Vocabulary Management

---

### F4.1 — Manual word entry

**Screen:** Vocab management  
**User story:** As a learner, I want to add individual words manually so that I can build my own custom vocabulary sets.

**Business rules:**
1. The Add Word form has two required fields: **Finnish word** and **English word**.
2. Both fields are required. Submitting with either empty triggers inline validation: "This field is required."
3. A topic must be assigned. The user selects from existing topics via a dropdown. If no topics exist, the user is prompted to create one first.
4. Duplicate detection: if a word with the exact same Finnish word (case-insensitive) already exists in the selected topic, a warning is shown: "This word already exists in [topic]. Do you want to overwrite it?" with options "Overwrite" and "Cancel".
5. On successful save, the word is added to the topic and the form resets to empty (ready for the next entry).
6. Finnish and English fields have a character limit of 100 characters each.

**Acceptance criteria:**
- [ ] Form has Finnish and English fields, both required.
- [ ] Topic selector populated from existing topics.
- [ ] Empty field submission shows inline validation error.
- [ ] Duplicate Finnish word in same topic triggers overwrite confirmation.
- [ ] Successful save resets the form.
- [ ] Character limit of 100 enforced on both fields.

---

### F4.2 — File import (JSON / CSV)

**Screen:** Vocab management  
**User story:** As a learner, I want to import a word list from a file so that I can bulk-add vocabulary quickly without typing each word manually.

**Business rules:**
1. Supported formats: **JSON** and **CSV**.
2. **JSON schema:**
   ```json
   {
     "topic": "Animals",
     "words": [
       { "finnish": "koira", "english": "dog" },
       { "finnish": "kissa", "english": "cat" }
     ]
   }
   ```
3. **CSV schema:** Header row required with columns `finnish` and `english` (case-insensitive). An optional `topic` column may be included; if absent, the user selects the target topic after upload.
4. Before confirming import, a preview table is shown with all parsed rows. Invalid rows are highlighted in red with an error message per row (e.g. "Missing English translation").
5. The user can proceed with valid rows only (skipping invalid rows) or cancel the entire import.
6. Duplicate detection: same rule as F4.1 — duplicates within the target topic show a warning. In bulk import, the user chooses "Overwrite all duplicates", "Skip all duplicates", or "Review one by one".
7. Maximum import size: 500 words per file.
8. On successful import, the user sees a confirmation: "X words imported successfully. Y rows skipped."

**Acceptance criteria:**
- [ ] JSON and CSV files are accepted.
- [ ] JSON and CSV schemas are validated; schema errors are reported clearly.
- [ ] Preview table shown before confirmation with valid and invalid rows distinguished.
- [ ] User can import valid rows and skip invalid rows.
- [ ] Duplicate handling offers Overwrite / Skip / Review options.
- [ ] Import capped at 500 words; file exceeding limit shows an error.
- [ ] Success confirmation shows imported count and skipped count.

---

### F4.3 — Topic management

**Screen:** Vocab management  
**User story:** As a learner, I want to create, rename, and delete vocabulary topics so that I can organise my word sets.

**Business rules:**
1. The user can **create** a new topic by entering a name. Topic name is required, max 50 characters, and must be unique (case-insensitive).
2. The user can **rename** an existing topic. Same validation rules as create. Renaming does not affect words or debt data associated with the topic.
3. The user can **delete** a topic. Deletion is blocked if the topic contains any words — the user sees: "Remove all words from this topic before deleting it." A future version may support force-delete with cascade, but not in v1.
4. Each topic in the list displays its word count.
5. Topics cannot be merged in v1.
6. There is no maximum number of topics in v1.

**Acceptance criteria:**
- [ ] Create topic form validates name length and uniqueness.
- [ ] Rename updates topic name without affecting associated words or debt data.
- [ ] Delete is blocked for topics with words; error message is shown.
- [ ] Word count displayed per topic in the list.

---

## F5 — Persistent Debt Across Sessions

**Screen:** System (background)  
**User story:** As a learner, I want my debt state to be saved when I exit a session so that unfinished work carries over to my next session automatically.

**Business rules:**
1. At the end of every session (completed or exited early), the full debt state is saved:
   - Per-word `debtCount` values.
   - In Hardcore Mode: per-word, per-type correctness map.
2. Debt state is written to **AsyncStorage** (offline-first) immediately on session end.
3. Debt state is then synced to **Supabase** in the background. If the device is offline, the sync is queued and retried when connectivity is restored.
4. When a new session starts with the same topic(s), the existing debt state for those words is loaded from AsyncStorage and merged into the new session queue.
5. Words carrying debt from a previous session appear in the session queue in addition to newly selected words (they do not count against the word count picker value — they are appended).
6. The user can manually **reset debt** for a topic or all topics from the Vocab Management screen. Reset clears all `debtCount` values and Hardcore per-type maps for the affected words.
7. Debt state is scoped per word ID, not per topic — if a word appears in multiple topics, its debt is shared.

**Acceptance criteria:**
- [ ] Debt state (debtCount + Hardcore map) is written to AsyncStorage at session end.
- [ ] Debt state is synced to Supabase; offline queue retries on reconnection.
- [ ] New session loads existing debt from AsyncStorage for selected topic words.
- [ ] Carried-over debt words are appended to the session queue without affecting the word count picker.
- [ ] Manual reset clears debtCount and Hardcore map for selected scope.
- [ ] Debt is scoped to word ID, not topic.

---

## F6 — Hint / Reveal in Typing Question

> Defined in F2.5 above. No additional standalone rules.

---

## F7 — Global Word Performance Tracking

**Screen:** System (background), surfaces in Summary and Dashboard  
**User story:** As a learner, I want each word to have a running performance history across all sessions so that I can see my true long-term weak points.

**Business rules:**
1. For every word in the vocabulary, the system maintains a `WordStats` record:
   - `totalCorrect`: total non-assisted correct answers across all sessions.
   - `totalWrong`: total wrong answers across all sessions.
   - `lastSeenAt`: timestamp of the last session in which the word appeared.
   - `assistedCorrect`: total assisted correct answers across all sessions (tracked separately).
2. `WordStats` is updated at the end of each session (including mini-sessions from F3.4).
3. `WordStats` is stored in AsyncStorage and synced to Supabase (same strategy as F5).
4. `WordStats` is used by:
   - Summary screen F3.2: most-missed words in the current session (session-level data, not global).
   - Dashboard F11.3: weakest words all-time (global `totalWrong` descending).
   - Dashboard F11.4: per-topic progress (derived from words' `totalCorrect` and `totalWrong`).
5. Deleting a word also deletes its `WordStats`.
6. Renaming or moving a word between topics preserves its `WordStats`.

**Acceptance criteria:**
- [ ] `WordStats` record exists for every word and is updated at session end.
- [ ] `totalCorrect` excludes assisted answers; `assistedCorrect` tracked separately.
- [ ] `lastSeenAt` updates after each session where the word appeared.
- [ ] Stats persist in AsyncStorage and sync to Supabase.
- [ ] Dashboard F11.3 and F11.4 use global stats correctly.
- [ ] Deleting a word removes its stats.
- [ ] Moving/renaming a word preserves its stats.

---

## F9 — Session History Log

**Screen:** Dashboard (surfaces in F11)  
**User story:** As a learner, I want a log of my past sessions so that I can track my progress over time.

**Business rules:**
1. After every session ends (completed or incomplete), a `SessionRecord` is saved containing:
   - `sessionId`: unique identifier.
   - `startedAt` / `endedAt`: timestamps.
   - `topics`: list of topic names used.
   - `wordCount`: number of unique words in the initial queue.
   - `totalCorrect`, `totalWrong`, `assistedCorrect`.
   - `accuracyPercent`: calculated at session end (excludes assisted).
   - `durationSeconds`: total elapsed time.
   - `hardcoreMode`: boolean.
   - `isIncomplete`: boolean (true if exited early).
2. Session records are stored in AsyncStorage and synced to Supabase.
3. There is no cap on the number of stored sessions in v1.
4. Session records are read-only — they cannot be edited or deleted by the user in v1.
5. Session history is consumed by Dashboard F11.1 (totals), F11.2 (accuracy trend chart).

**Acceptance criteria:**
- [ ] A `SessionRecord` is created and saved after every session including mini-sessions.
- [ ] All required fields are populated correctly.
- [ ] Records persist in AsyncStorage and sync to Supabase.
- [ ] `isIncomplete = true` for sessions exited early.
- [ ] Dashboard F11.1 and F11.2 correctly consume session history.

---

## F10 — Quick Review / Flashcard Mode

**Screen:** Quick review (separate from quiz flow)  
**User story:** As a learner, I want to browse through words as flashcards before a quiz so that I can warm up without scoring pressure.

**Business rules:**
1. Quick Review is accessible from the Setup screen as a secondary action (e.g. "Review first" link).
2. It uses the same topic selection as currently configured in Setup (F1.1). If no topics are selected, the user is prompted to select one.
3. Cards are displayed one at a time. The front of the card shows the Finnish word; tapping flips to reveal the English word (and vice versa — the card is two-sided).
4. The user swipes left/right or taps Next/Previous to navigate through the cards.
5. Cards are shown in random order. The user can reshuffle at any time.
6. **No scoring, no debt, no timer** — Quick Review is purely informational.
7. Exiting Quick Review returns the user to the Setup screen with the same configuration intact.
8. Quick Review does not affect `WordStats` (F7) or session history (F9).

**Acceptance criteria:**
- [ ] Quick Review accessible from Setup screen.
- [ ] Cards use selected topics from F1.1; prompts if no topic selected.
- [ ] Card flip reveals translation; flip is animated.
- [ ] Swipe or Next/Previous navigation works.
- [ ] Cards presented in random order; reshuffle button available.
- [ ] No scores, debt, or timer shown.
- [ ] Exiting returns to Setup with config unchanged.
- [ ] No impact on WordStats or session history.

---

## F11 — Learning Dashboard

**Screen:** Dashboard  
**User story:** As a learner, I want a dashboard that summarises my entire learning journey so that I can see my overall progress and identify long-term weak areas.

---

### F11.1 — Overall progress overview

**Screen:** Dashboard  
**User story:** As a learner, I want to see my all-time study stats at a glance so that I can measure how much I have studied overall.

**Business rules:**
1. Displays the following all-time metrics, derived from session history (F9):
   - **Total sessions:** count of all `SessionRecord` entries (including incomplete).
   - **Total words studied:** sum of `wordCount` across all sessions (counts repetitions).
   - **Overall accuracy:** `sum(totalCorrect) / (sum(totalCorrect) + sum(totalWrong)) * 100`, rounded to 1 decimal. Excludes assisted answers.
   - **Total study time:** sum of `durationSeconds` across all sessions, displayed as "Xh Ym".
2. If no sessions have been completed yet, a zero/empty state is shown: "Start your first session to see your stats."

**Acceptance criteria:**
- [ ] All 4 metrics are displayed and calculated correctly from session history.
- [ ] Assisted answers excluded from accuracy calculation.
- [ ] Empty state shown when no sessions exist.

---

### F11.2 — Accuracy trend over time

**Screen:** Dashboard  
**User story:** As a learner, I want to see a chart of my accuracy across sessions so that I can see if I am improving over time.

**Business rules:**
1. Displays a line chart where each data point represents one session's `accuracyPercent`.
2. X-axis: sessions in chronological order (oldest to newest).
3. Y-axis: accuracy percentage (0–100%).
4. The user can filter by time range: **Last 7 sessions**, **Last 30 sessions**, **All sessions**.
5. The user can filter by topic: show only sessions that included a specific topic.
6. Incomplete sessions are included in the chart but displayed with a distinct marker (e.g. hollow dot vs solid dot).
7. If fewer than 2 sessions exist, the chart is replaced with a message: "Complete at least 2 sessions to see your trend."

**Acceptance criteria:**
- [ ] Line chart renders with correct x/y axes.
- [ ] Data points match session accuracy values from F9 records.
- [ ] Time range filter (7 / 30 / all) works correctly.
- [ ] Topic filter shows only sessions containing the selected topic.
- [ ] Incomplete sessions shown with distinct visual marker.
- [ ] Fewer than 2 sessions shows placeholder message.

---

### F11.3 — Weakest words all-time

**Screen:** Dashboard  
**User story:** As a learner, I want to see which words I have consistently struggled with across all sessions so that I can target my study efforts.

**Business rules:**
1. Displays the **top 10 words** ranked by `totalWrong` descending (from `WordStats`, F7).
2. Each entry shows: Finnish word, English word, total wrong count, and total correct count.
3. A "Drill these words" button launches a mini-session (same as F3.4) using these top 10 words.
4. If fewer than 10 words have any wrong answers, only words with `totalWrong > 0` are shown.
5. If no words have ever been answered incorrectly, an empty state is shown: "No weak words yet — keep practising!"

**Acceptance criteria:**
- [ ] Top 10 words by totalWrong shown with Finnish, English, wrong count, correct count.
- [ ] "Drill these words" launches mini-session with these words.
- [ ] Empty state shown when totalWrong = 0 for all words.
- [ ] List updates in real-time as WordStats are updated after each session.

---

### F11.4 — Per-topic progress

**Screen:** Dashboard  
**User story:** As a learner, I want to see how well I know each topic so that I can identify which topics need more practice.

**Business rules:**
1. Displays a list of all topics with the following metrics per topic, derived from `WordStats` (F7):
   - **Words in topic:** total word count.
   - **Accuracy %:** `sum(totalCorrect for words in topic) / (sum(totalCorrect + totalWrong) for words in topic) * 100`. Words never seen have accuracy shown as "—".
   - **Last studied:** most recent `lastSeenAt` among all words in the topic. Shows "Never" if no session has included this topic.
2. Topics are sorted by accuracy ascending (weakest topics first) to surface areas needing attention.
3. Tapping a topic navigates to a detail view showing all words in that topic with their individual `WordStats`.
4. Topics with 0 words are shown but all metrics show "—".

**Acceptance criteria:**
- [ ] All topics listed with word count, accuracy %, and last studied date.
- [ ] Accuracy calculated correctly from WordStats; never-seen words shown as "—".
- [ ] Topics sorted by accuracy ascending.
- [ ] Tapping topic opens per-word stats detail view.
- [ ] Topics with 0 words display "—" for all metrics.

---

*End of Section 6 — Feature List*
