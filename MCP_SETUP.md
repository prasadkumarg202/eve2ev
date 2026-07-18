# MCP Servers — Ev2Ev

This project ships a committed [`.mcp.json`](.mcp.json) that wires up the MCP
servers used to research, design, build, test, and operate Ev2Ev. Credentials
are **never** hard-coded — `.mcp.json` references `${ENV_VARS}` that Claude Code
expands from your environment at launch.

## How it works

1. Copy the credential template and fill in the keys you have:
   ```bash
   cp .env.mcp.example .env.mcp     # then edit .env.mcp
   ```
2. Load them into your environment **before** starting Claude Code (Claude Code
   expands `${VAR}` in `.mcp.json` from the process env, not from a file):
   ```bash
   set -a; source .env.mcp; set +a   # bash / git-bash
   claude
   ```
   (PowerShell: set each with `$env:NAME = "value"`, or use a tool like `direnv`.)
3. On first load Claude Code shows a **workspace-trust prompt** for `.mcp.json`.
   Approve it. Then run `/mcp` (or `claude mcp list`) to see connection status
   and to complete OAuth for servers that use it (Figma Dev Mode, Razorpay).
4. A server whose env var is unset stays listed but shows "needs auth" — it
   simply won't be usable until you provide the key. Nothing else breaks.

## Server status

| Server | Works now? | Needs | Notes |
|---|---|---|---|
| **filesystem** | ✅ yes | — | Scoped to `D:/websites/Ev2Ev` |
| **playwright** | ✅ yes | — | Browser automation; downloads browsers on first use |
| **context7** | ✅ yes | optional `CONTEXT7_API_KEY` | Up-to-date library/API docs; key raises limits |
| **browser** | ✅ (with ext) | Browser MCP Chrome extension | Drives your real logged-in Chrome |
| **github** | 🔑 | `GITHUB_PERSONAL_ACCESS_TOKEN` | Repos/issues/PRs |
| **supabase** | 🔑 | `SUPABASE_ACCESS_TOKEN`, `SUPABASE_PROJECT_REF` | `--read-only`; also available via your claude.ai Supabase connector |
| **postgres** | 🔑 | `DATABASE_URL` | via `@bytebase/dbhub`; point at the Supabase Postgres DSN |
| **firecrawl** | 🔑💳 | `FIRECRAWL_API_KEY` | Web scraping/crawl (paid) |
| **brave-search** | 🔑 | `BRAVE_API_KEY` | Web search (free tier) |
| **tavily** | 🔑 | `TAVILY_API_KEY` | Search alternative (freemium) |
| **figma** | 🔑 | `FIGMA_API_KEY` | Design → code (Framelink). Dev-Mode remote is an alt |
| **slack** | 🔑 | `SLACK_BOT_TOKEN`, `SLACK_TEAM_ID` | Also available via your claude.ai Slack connector |
| **twilio** | 🔑💳 | `TWILIO_ACCOUNT_SID`, `TWILIO_API_KEY`, `TWILIO_API_SECRET` | SMS/voice (paid) |
| **razorpay** | 🔑 | OAuth on connect | Remote MCP `https://mcp.razorpay.com/mcp`; payments |

Legend: ✅ ready · 🔑 needs credentials · 💳 paid account

## Already available via your claude.ai account

`claude mcp list` shows these remote connectors already attached to your
account (no `.mcp.json` entry needed — authenticate with `/mcp`):
**Supabase** (connected), **Slack**, **Gmail**, **Google Drive**, Notion.
The `.mcp.json` entries above are the project-local, portable equivalents so the
setup is reproducible for anyone who clones the repo.

## Package pins (verified on npm)

All server packages in `.mcp.json` were verified to exist:
`@modelcontextprotocol/server-filesystem`, `@playwright/mcp`,
`@upstash/context7-mcp`, `@modelcontextprotocol/server-github`,
`@supabase/mcp-server-supabase`, `@bytebase/dbhub`, `firecrawl-mcp`,
`@brave/brave-search-mcp-server`, `tavily-mcp`, `figma-developer-mcp`,
`@browsermcp/mcp`, `@modelcontextprotocol/server-slack`, `@twilio-alpha/mcp`.

## Notes on companions

- **Browser MCP** needs the *Browser MCP* Chrome extension installed + enabled.
- **Figma**: the Framelink server (used here) needs a Figma personal access
  token. Alternatively, Figma's official Dev-Mode MCP runs locally inside the
  Figma **desktop** app — add it with
  `claude mcp add --transport http figma-devmode http://127.0.0.1:3845/mcp`.
- **Razorpay/Twilio/Firecrawl** require paid/production accounts.
