# MadeSimple Workshop — AI Skills

AI Skills to help in many different technical and non-technical tasks, by
[MadeSimple Workshop](https://github.com/MadeSimpleWorkshop). Free for
personal and noncommercial use — see [License at a glance](#license-at-a-glance).

These skills follow the open [Agent Skills](https://agentskills.io) standard
(`SKILL.md`), so they work in **Claude Code, claude.ai, OpenAI Codex, ChatGPT,
Cursor, GitHub Copilot, Gemini CLI**, and dozens of other AI agents.

## Install

Pick the approach that matches how you use AI. (Full step-by-step directions
for each are in [INSTALL.md](./INSTALL.md).)

### 1. Ask your AI to install it (easiest — works anywhere)

Copy this whole block and paste it into your AI assistant (Claude Code, Codex,
Cursor, Copilot, Gemini CLI, etc.):

```text
Please install the AI skills from https://github.com/MadeSimpleWorkshop/skills

Do it the simplest way that works in this environment, trying in this order:
1. If the `skills` CLI works here, run: npx skills add MadeSimpleWorkshop/skills
   and let me pick which skills to install.
2. If you are Claude Code and plugins are available, run:
   /plugin marketplace add MadeSimpleWorkshop/skills
   then: /plugin install madesimple-skills@madesimple
3. If you are OpenAI Codex, use your skill installer on:
   https://github.com/MadeSimpleWorkshop/skills/tree/main/skills
4. Otherwise, clone the repo and copy the folders under skills/ into my
   agent's skills directory (for example ~/.claude/skills/ for Claude Code
   or ~/.agents/skills/ for Codex), keeping each folder's LICENSE.md.

When you're done, list the skills that were installed and give me one
example prompt for each. These skills are licensed PolyForm Noncommercial
1.0.0 + no-AI-training; keep the license files with the copies.
```

### 2. One command in your terminal (any coding agent)

Installs into Claude Code, OpenAI Codex, Cursor, Copilot, Gemini CLI, and ~40
other agents at once — it auto-detects what you have:

```bash
npx skills add MadeSimpleWorkshop/skills                     # pick from all 6
npx skills add MadeSimpleWorkshop/skills --list              # preview first
npx skills add MadeSimpleWorkshop/skills -s image-upscale    # just one skill
npx skills add MadeSimpleWorkshop/skills -g                  # all projects (global)
```

### 3. Claude Code plugin marketplace

Inside Claude Code:

```
/plugin marketplace add MadeSimpleWorkshop/skills
/plugin install madesimple-skills@madesimple
```

### 4. OpenAI Codex

Ask Codex to install a skill by URL, or use its skill installer:

```
$skill-installer install https://github.com/MadeSimpleWorkshop/skills/tree/main/skills/image-upscale
```

### 5. claude.ai / ChatGPT — no terminal needed

1. Download the zip for the skill you want from
   **[Releases](https://github.com/MadeSimpleWorkshop/skills/releases)**.
2. Upload it: **claude.ai** → Settings → Capabilities → Skills;
   **ChatGPT** → Skills → New skill → Upload.
3. Toggle it on and just ask for what it does.

### 6. Manual (git)

```bash
git clone https://github.com/MadeSimpleWorkshop/skills.git
cp -R skills/skills/* ~/.claude/skills/    # Claude Code (all projects)
cp -R skills/skills/* ~/.agents/skills/    # Codex / cross-agent standard
```

### Try one before installing

```bash
npx skills use MadeSimpleWorkshop/skills@sitemap-xml-generator
```

This generates a one-off prompt for a single skill without installing anything.

## The skills

| Skill | What it does |
|---|---|
| [frequency-tone-generator](./skills/frequency-tone-generator/) | Generate exact-length layered frequency-tone audio (WAV) for meditation music, solfeggio tones, or YouTube audio beds |
| [image-upscale](./skills/image-upscale/) | Upscale photos, screenshots, and artwork (2x/4x, target resolutions, batch folders) with backend selection guidance |
| [sitemap-xml-generator](./skills/sitemap-xml-generator/) | Generate a standards-compliant sitemap.xml for Google/Bing from a local site build, plus robots.txt wiring |
| [youtube-to-suno-prompts](./skills/youtube-to-suno-prompts/) | Turn a reference track you own into Suno prompt variants (genre/mood/instrumentation) without copying lyrics or melodies |
| [web-builder-youtube-patreon](./skills/web-builder-youtube-patreon/) | Build and optimize websites that funnel traffic to your YouTube and Patreon |
| [website-color-pattern-redesign](./skills/website-color-pattern-redesign/) | Audit and modernize a site's color system and visual patterns with safe, previewable rollout |

Skills activate automatically when your request matches what they do — no
special commands to memorize.

## License at a glance

This repository is **source-available, not open source.** It is licensed under
the **[PolyForm Noncommercial License 1.0.0](./LICENSE.md)** plus an
**AI & Machine Learning Addendum**. In plain terms:

| You want to… | Allowed? |
|---|---|
| Use these skills for **personal, hobby, study, or non-commercial** work | ✅ Yes, free |
| Use them inside a **non-profit, school, or government** setting | ✅ Yes, free |
| **Modify** them for your own non-commercial use | ✅ Yes |
| **Share** copies (keeping the license + notices intact) | ✅ Yes |
| Use them in a **product, paid service, or anything commercial** | 💼 Yes — with a paid [commercial license](#commercial-licensing) |
| Use them to **train, fine-tune, or build AI/ML models or datasets** | ❌ Never, under any terms |

> ⚠️ This is a summary for convenience only. The full, binding terms are in
> [`LICENSE.md`](./LICENSE.md). If the summary and the license ever disagree,
> the license wins.

### No AI training

No permission is granted to use anything in this repository — in whole or in
part — to train, fine-tune, evaluate, benchmark, distill, or otherwise develop
any machine-learning or artificial-intelligence model, system, or dataset. See
the **AI & Machine Learning Addendum** in [`LICENSE.md`](./LICENSE.md).

### Commercial licensing

Any commercial or product use requires a separate written license. Reach out via
GitHub:

**MadeSimple Workshop** — <https://github.com/MadeSimpleWorkshop>

### Contributions

Contributions are welcome, but by submitting one you agree it is licensed under
the same terms and that MadeSimple Workshop may relicense it (including
commercially). See section 6 of the Addendum in [`LICENSE.md`](./LICENSE.md).

---

© 2026 MadeSimple Workshop. All rights reserved.
