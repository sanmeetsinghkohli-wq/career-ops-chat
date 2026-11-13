# Career-Ops Chat

**Turn Claude into your job-search assistant: no coding, no installs, free to use.**

Career-Ops Chat is a Claude skill that turns any normal Claude chat into a job-search copilot. Paste a job link and get an honest fit score. Find live internships and jobs, tailor your CV, check how applicant-tracking software reads it, and prepare for interviews. It all runs on Claude web, desktop and mobile.

> Community project, not affiliated with Anthropic. Adapted from the open-source [career-ops](https://github.com/career-ops-hq/career-ops) project by Santiago Fernández de Valderrama (MIT licence).

---

## Features

| | What it does |
|---|---|
| 🎯 **Evaluate any job** | A fit score from 1 to 5, a requirement-by-requirement CV match, gaps with mitigations, pay research and a posting-legitimacy check |
| 🔍 **Find jobs** | Searches the web for live openings that match your profile, checked on employer sites where possible |
| 📄 **Tailored CV** | A CV rewritten for one job, using only facts already in your CV, plus a list of what changed |
| ✅ **ATS check** | A score from 0 to 100 from career-ops' own scoring script (`verify-ats.mjs`), never estimated by the AI |
| ✉️ **Cover letters and outreach** | Cover letters, recruiter and hiring-manager messages, and follow-ups |
| 🎤 **Interview prep** | Likely questions, STAR+R stories built from your CV, and mock interviews with feedback |
| 📊 **Tracking** | An application tracker, offer comparison and negotiation prep |

### Ground rules the skill always follows
- **Never invents facts.** Your CV is the only source of truth.
- **Never sends anything for you.** You review every draft and apply yourself.
- **Honest scores.** Below 4.0/5, it recommends against applying.
- **Verified links.** Job-board copies are marked "unconfirmed".
- **Scam awareness.** It flags requests for payment and unclear employers.

---

## Install (about 2 minutes)

**You need:** a Claude account (Free, Pro or Max). On Team or Enterprise accounts, an admin must allow skills.

1. **Download** [`career-ops-chat.zip`](https://github.com/sanmeetsinghkohli-wq/career-ops-chat/raw/main/career-ops-chat.zip). Don't unzip it.
2. In Claude, open **Settings → Capabilities** and switch on **Code execution and file creation** (called *Create and edit files* in newer Settings). The ATS check needs it.
3. Go to **Customize → Skills → + → Create skill → Upload a skill** and select the zip.
4. Make sure **career-ops-chat** is switched **on**.
5. Turn on **web search** in the chat's tools menu so the skill can find jobs and read links.

See Anthropic's guide: [Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills).

---

## Usage

Start a new chat, attach your CV (Word or PDF) and type a command:

```
Use career-ops-chat. Here's my CV. Find me paid AI internships in Dubai.
career-ops-chat: evaluate this job: <job link>
career-ops-chat ats
career-ops-chat: tailor my CV for this job: <job link>
career-ops-chat: interview prep for <company and role>
```

### Commands

| Command | Output |
|---|---|
| *(paste a job link)* | Fit score, then a tailored CV, cover letter and interview prep if the score is 4.0 or higher |
| `evaluate` | Full fit report with a 1–5 score |
| `triage` | Quick apply / maybe / skip for several jobs |
| `find` | Live openings that match your profile |
| `compare` | Several jobs or offers ranked side by side |
| `cv` | A CV tailored to one job |
| `ats` | ATS score from 0 to 100 from the bundled script |
| `cover` | Cover letter |
| `outreach` | Recruiter, hiring-manager or alumni messages |
| `company` | Company research with sources |
| `interview-prep` / `mock` | Interview prep and mock interviews |
| `tracker` / `followup` | Application tracker and follow-up drafts |
| `offer` | Offer review and negotiation points |
| `upskill` / `titles` | Skill gaps and other job titles to search |

> Every new chat starts empty. Save your profile, tailored CVs and tracker at the end of a session, and re-attach them next time.

---

## How the ATS check works

```
your CV (.docx / .pdf / .md / .txt)
        │
        ▼
scripts/cv_to_html.py        converts the file only: headings → <h2>, tables, images, fonts
        │
        ▼
scripts/verify-ats.mjs       career-ops' own scorer, unmodified: 0–100 score, grade and issues
        │
        ▼
Claude reports the exact score and every issue, with fixes
```

The scorer checks for readable text, standard headings (Experience, Education, Skills), contact details, single-column layout, tables, text inside images, fonts, and hidden text. Grades: **A** is 90+, **B** 80+, **C** 70+, **D** 60+, and **F** is below 60.

**Tip:** check the **Word** version of your CV for the most accurate result. A PDF only records where text sits on the page, so headings are detected from bold or large text.

---

## Repository structure

```
career-ops-chat/
├── SKILL.md                    # instructions Claude follows
└── scripts/
    ├── verify-ats.mjs          # career-ops ATS scorer (unmodified)
    ├── lib/                    # its two helper modules (unmodified)
    ├── cv_to_html.py           # CV → HTML converter (no scoring)
    ├── LICENSE-career-ops      # MIT licence of the original project
    └── CAREER_OPS_COMMIT       # upstream commit the scorer was taken from
```

`career-ops-chat.zip` in the repo root is the ready-to-upload skill. To rebuild it from the source files:

```bash
zip -r career-ops-chat.zip career-ops-chat
```

---

## Credits and licence

- **Original project:** [career-ops](https://github.com/career-ops-hq/career-ops) by Santiago Fernández de Valderrama, MIT licence. The ATS scorer and its helper modules are included unmodified under that licence.
- **Career-Ops Chat:** adapted for regular Claude chats by **Sanmeet Singh Kohli**.

Released under the MIT licence. See `LICENSE`.

Feedback and pull requests are welcome.
