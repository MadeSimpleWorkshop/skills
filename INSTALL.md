# Installing these skills

Pick whichever path matches how you use AI. Every path below is free for
personal/noncommercial use — see [LICENSE.md](./LICENSE.md).

---

## Option 1 — Let your AI install it for you (easiest)

Copy this entire block and paste it into your AI coding assistant
(Claude Code, Codex, Cursor, Copilot, Gemini CLI, etc.):

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

## Option 2 — One command in your terminal

Works for Claude Code, OpenAI Codex, Cursor, Copilot, Gemini CLI, and ~40
other agents at once (it auto-detects what you have installed):

```bash
npx skills add MadeSimpleWorkshop/skills
```

Useful variants:

```bash
npx skills add MadeSimpleWorkshop/skills --list        # preview the skills first
npx skills add MadeSimpleWorkshop/skills -s image-upscale   # install just one
npx skills add MadeSimpleWorkshop/skills -g            # install globally (all projects)
```

## Option 3 — Claude Code plugin marketplace

Inside Claude Code:

```
/plugin marketplace add MadeSimpleWorkshop/skills
/plugin install madesimple-skills@madesimple
```

## Option 4 — claude.ai or ChatGPT (no terminal needed)

1. Go to this repo's **[Releases page](https://github.com/MadeSimpleWorkshop/skills/releases)**
   and download the `.zip` for the skill you want.
2. Upload it:
   - **claude.ai** — Settings → Capabilities → **Skills** → upload the zip.
     (Enable code execution first if prompted.)
   - **ChatGPT** — Skills → **New skill → Upload** the zip.
3. Toggle the skill on and just ask for what it does — it activates
   automatically when relevant.

## Option 5 — Manual (git)

```bash
git clone https://github.com/MadeSimpleWorkshop/skills.git
# Claude Code (personal, all projects):
cp -R skills/skills/* ~/.claude/skills/
# OpenAI Codex / cross-agent standard location:
cp -R skills/skills/* ~/.agents/skills/
# Or per-project: copy into .claude/skills/ or .agents/skills/ in your repo
```

---

## After installing

Skills activate automatically when your request matches their description —
you don't need to memorize commands. Try:

- "Generate a 10-minute 432 Hz meditation tone" (*frequency-tone-generator*)
- "Upscale this photo to 4x" (*image-upscale*)
- "Create a sitemap.xml for my site's dist folder" (*sitemap-xml-generator*)
- "Make Suno prompts inspired by this track I own" (*youtube-to-suno-prompts*)
- "Build a landing page that drives traffic to my YouTube and Patreon" (*web-builder-youtube-patreon*)
- "Audit and refresh my site's color palette" (*website-color-pattern-redesign*)

## License reminder

These skills are **free for personal and noncommercial use** under
[PolyForm Noncommercial 1.0.0 + AI/ML Addendum](./LICENSE.md). Keep the
`LICENSE.md` bundled in each skill folder when you share copies. Want to use
them in a product or paid service? Commercial licenses are available —
[get in touch](https://github.com/MadeSimpleWorkshop). Never use these
files to train or fine-tune AI/ML models.
