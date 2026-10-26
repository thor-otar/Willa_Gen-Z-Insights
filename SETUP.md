# Gen Z Insight Agent — setup and maintenance

Same setup as the Wren & Willa agent: a private chat page plus one server function that talks to Claude. Use a new GitHub repo and a new Vercel project.

## Deploy
1. Anthropic Console: use your existing API key or create a new one. Keep the monthly spend limit on.
2. GitHub: new private repo (e.g. `genz-insight-agent`). Upload everything in this folder.
3. Vercel: import the repo (preset: Other) and set these environment variables, then deploy:
   - `ANTHROPIC_API_KEY` = your key
   - `ACCESS_CODES` = the line below (rename the labels to people's names)
   - `MODEL` (optional) = `claude-sonnet-5-5` by default
4. Test all three functions before showing anyone.

## Access codes (10 people)
```
person1:gz-hp4ekf,person2:gz-48riy6,person3:gz-nwtbuk,person4:gz-xwk7gw,person5:gz-2nv83z,person6:gz-2a8imh,person7:gz-khfmfx,person8:gz-hw7mk4,person9:gz-i76r7a,person10:gz-px8gp6
```

## How it works
- `public/library.json` is what people see: insight cards, formats, touchpoints and the fit matrix. Cards are rendered from this file, so the numbers on cards always match the library.
- `lib/knowledge.js` is what Claude reads: the agent instructions plus the same library in compact form, sent with every message and cached.
- `lib/modes.js` holds the three functions (Explore insights, Test an idea, Find carriers).
- Carrier cards are checked against the fit matrix in the browser. If Claude proposes a pair that isn't in the matrix, the card says so.

## Updating the library
The library is generated from `data/insights_raw.txt` (one insight per line, fields separated by ~) and the formats report. Send changes to Claude and ask it to regenerate `library.json` and `knowledge.js`, or run `python3 data/build_data.py` and copy the outputs into `public/` and `lib/`.

## Good to know
- Conversations stay in each person's browser; nothing is stored on the server. The Board (saved cards) is per browser too; "Copy all" exports it as text.
- Vercel logs show which label used the agent and which function.

## Web search (new)
- When the library can't answer, the agent can search the web (up to 3 searches per answer). New facts appear as dashed "new · web" cards with the source link, kept separate from library cards.
- A card warns if its link wasn't among the actual search results, and every new card says it hasn't been reviewed by COBRA.
- Users can switch web search off per browser (checkbox above the input). To switch it off for everyone, set `WEB_SEARCH=off` in Vercel. `MAX_SEARCHES` changes the per-answer limit (default 3).
- Setup: web search must be enabled for your organization in the Anthropic Console. It's billed per search on top of tokens (check the current price in Anthropic's docs).
- Growing the library: every new finding is logged in Vercel's logs as a line starting with `CANDIDATE_INSIGHT`. Users can also press "Propose for library", which puts the card on their Board. Review candidates regularly; the ones that hold up go into `data/insights_raw.txt`.
- Searches make answers slower (often 20–40 seconds). The function time limit is set to 120 seconds in `vercel.json`; if your Vercel plan rejects that, set it to 60.

## Client data
See CLIENT-DATA.md.
