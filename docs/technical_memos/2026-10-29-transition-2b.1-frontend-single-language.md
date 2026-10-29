# Technical Memo: Transition-2B.1 — Frontend Single-Language & RAG Citation Boundary Fix

- **Date:** 2026-10-29
- **Iteration:** Transition-2B.1 (Agile Unified Process - Craig Larman)
- **Tag:** `transition-2b.1`
- **Scope:** Frontend Single-Language (English only) + Fix AI Feedback Truncation

---

## 1. Problem Statement

### 1.1 Inconsistent UI Language (False Positive Verification in 2B)
In iteration Transition-2B, backend tests passed and API responses were returned in English. However, visual verification of the user interface revealed that:
- `useTranslation` in `frontend/src/i18n/translations.js` contained a structural fallback bug that mapped unrecognized locales to Spanish.
- Over 100 hardcoded Spanish and Portuguese strings persisted across 10 JSX components (e.g. `isPt ? ... : ...`).
- Language selector dropdown `<select>` was exposed to users despite the system standardizing on English.

### 1.2 Truncated RAG Citations (`...University (p.`)
When Gemini generated pedagogical feedback citing the reference book, the text was truncated mid-parenthesis:
```
"...as recommended in Jiu-Jitsu University (p."
```
**Root cause analysis:**
`GeminiApiAdapter._limpiar_feedback` split sentences using `re.split(r"(?<=[.!?])\s+", texto)`. Because citations contained abbreviated page numbers like `(p. 116)`, the dot in `p.` was treated as a full sentence delimiter. When `frases[:2]` extracted the first two sentences, the sentence was chopped right after `(p.`, and `max_words=45` capped the output before closing.

---

## 2. Architectural Decisions & Solutions

### 2.1 Single-Language English Architecture (Frontend)
Per Larman's UP principle of avoiding accidental complexity when requirements clarify:
1. Removed the i18n subsystem entirely: deleted `frontend/src/i18n/translations.js` and `frontend/src/i18n/`.
2. Removed all `useTranslation` hook usages, `t.xxx` translation references, and language selector dropdowns.
3. Hardcoded English cleanly across all 10 JSX components:
   - `App.jsx`
   - `FeedbackView.jsx`
   - `VideoUpload.jsx`
   - `AdminSucursales.jsx`
   - `ProfesorTecnicas.jsx`
   - `StudentProgress.jsx`
   - `SelectorPersonaVideo.jsx`
   - `TheoryManagerModal.jsx`
   - `GlobalKnowledgeModal.jsx`
   - `UserProfileModal.jsx`
   - `LoginModal.jsx`

### 2.2 Citation-Safe Sentence Boundary & Word Limit Expansion
1. **Word Limit:** Increased limit in `EnglishPromptStrategy` from 45 to 60 words.
2. **Token Limit:** Increased `max_output_tokens` in `GeminiApiAdapter.generar_texto_feedback` to 500.
3. **Regex Fix:** Changed sentence splitting regex to `re.split(r"(?<=[.!?])\s+(?=[A-Z¿¡])", texto)`. Sentences are now split only when punctuation is followed by an uppercase letter or question/exclamation mark. Abbreviations like `p. 116` or `e.g. 5` are preserved intact.
4. **Unclosed Parenthesis Guard:** If an open parenthesis `(` is detected without a corresponding closing parenthesis `)` later in the string, `_limpiar_feedback` rolls back cleanly before the opening `(`.
5. **Punctuation Guarantee:** Ensures the output string terminates with valid terminal punctuation (`.`, `!`, `?`, or `)`).

---

## 3. Verification & Evidence

### 3.1 Grep Controls
- Accents / special characters in JSX strings: **0 matches**
- `useTranslation` in `frontend/src`: **0 matches**
- `t.xxx` translation lookups: **0 matches**
- Language options / selectors: **0 matches**

### 3.2 Compilation & Unit Tests
- `vite build`: 51 modules transformed, `dist/index.html` built in 361ms with 0 errors.
- `pytest`: 36 passed, 1 skipped in 0.06s.

### 3.3 End-to-End Analysis (`Alumno.mp4`)
- Executed in **12.11s**.
- Biomechanical similarity: **25.72%**.
- Resulting feedback:
  > *"You are letting your framing arm get isolated and flattened instead of keeping your elbow tucked tightly in front of Xande's hip as taught in Jiu-Jitsu University (p. 116). Keep your elbow actively posted to maintain structural integrity and prevent him from passing your defense."*
- Full citation preserved: `(p. 116).`

### 3.4 Visual Evidence (Playwright)
Screenshots captured before and after in `/tmp/baseline_before/` vs `/tmp/baseline_after/`:
- `login.png`
- `upload.png`
- `feedback.png`
- `admin.png`
