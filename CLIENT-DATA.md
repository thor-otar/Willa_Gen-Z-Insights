# Adding Vera Bradley's interviews and panel data

Client data is the agent's strongest differentiator: no general chatbot has it. It enters the library as V-tier findings, ranked above third-party data for questions about Vera Bradley's own customers.

## What to send (and what not to)
- Interviews: transcripts or notes, plus the brief (who, how many, how recruited, when). I code them into findings (one claim each), with counts like "9 of 14" rather than percentages for small samples. Short paraphrases only; no names, handles, schools, cities or anything else that identifies a participant.
- Panel: the questionnaire plus aggregated results (cross-tabs by age and segment). Respondent-level files aren't needed and shouldn't be loaded.
- Confirm with Vera Bradley before loading that their agreement with participants allows this use, and that the data may be processed by Anthropic's API.

## How it works
- Findings go in `data/client_raw.txt` (format in `client_raw.example.txt`). Rebuild the library and redeploy.
- V-findings appear as cards with a "V" grade and the method and sample on every card.
- Keep one deployment per client. Never load Vera Bradley data into an agent other clients can access.

## Why this matters for the product
The agent's answers become a three-way synthesis no one else can produce: third-party evidence (library), fresh evidence (web, labelled as new), and Vera Bradley's own customers (V). The instructions already tell the agent to triangulate and to say where the sources disagree.
