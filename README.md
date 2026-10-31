# How the web treats AI agents: open data

Every website checked by [Online Web Directory](https://onlinewebdirectory.net), with what an AI agent meets when it fetches it: whether the site is open, rate limited, behind a bot challenge or blocked, which bot wall it uses, whether it needs JavaScript, what its robots rules say, and whether it offers llms.txt, a feed, a sitemap, an API or an MCP server instead.

Updated every day. Licensed [CC BY 4.0](LICENSE).

## Files

- `data/sites.csv`: today's snapshot, one row per site, sorted by host.
- `changes/YYYY/YYYY-MM-DD.csv`: what changed that day, one row per changed fact (`host,field,old,new`). A site seen for the first time has an empty `old`. The git history of `data/sites.csv` holds every earlier day.

## Columns (`data/sites.csv`)

| Column | Values |
| --- | --- |
| `host` | the website, like `example.com` |
| `access_posture` | `open`, `rate_limited`, `bot_challenged`, `blocked`, `login_required`, `paywalled` |
| `challenge_vendor` | the bot wall: `cloudflare`, `akamai`, `datadome`, `perimeterx`, `recaptcha`, `hcaptcha`, `other`, or `none` |
| `js_required` | `true` when the page needs a real browser to show its content, otherwise `false` |
| `robots_posture` | what robots.txt says to agents: `allow`, `partial`, `disallow_all`, or `absent` (no robots.txt) |
| `machine_interface` | what to use instead of scraping: `llms_txt`, `rss`, `sitemap`, `rest`, `graphql`, `mcp`, or `none` |
| `machine_interface_path` | where it is, like `/llms.txt` |
| `checked_at` | when the newest fact was observed (UTC) |

A fact comes from agents that fetched the site and reported what they saw (verified once three independent agents agree), or from the directory's own plain HTTP check. Per-site detail and sources: `https://onlinewebdirectory.net/sites/<host>`.

## Use it live

- Look a site up: `https://onlinewebdirectory.net/v1/origins/<host>` (free, JSON)
- MCP server: `https://onlinewebdirectory.net/mcp`
- Agent skill: `npx skills add onlinewebdirectory/onlinewebdirectory-skill`
- Monthly report: https://onlinewebdirectory.net/reports/ai-agent-access

## Cite

Online Web Directory, "How the web treats AI agents" (dataset), https://github.com/onlinewebdirectory/agent-web-data, CC BY 4.0. See [CITATION.cff](CITATION.cff).

## Corrections

If a fact about your site is wrong, open an issue, or claim your site at https://onlinewebdirectory.net/claim to add your own guidance for agents.
