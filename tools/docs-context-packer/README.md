# docs-context-packer

Pack public documentation URLs into agent-ready context — **compliant fetch for agents** via withOhm `ohm_fetch_web`.

This tool does not scrape by itself. It expects Ohm MCP (or the Ohm HTTP pipe). You install the packer skill; Ohm rides along.

## Why

Agents stall without page text. Hand-browsing does not scale. This packer turns a list of public docs URLs into one context blob you can paste or feed through Ohm.

## Setup

1. Attach withOhm: https://withohm.dev/i  
2. Copy `skills/docs-context-packer/SKILL.md` into your project `.cursor/skills/` (or use from this folder).
3. Or run the CLI (calls Ohm HTTP):

```bash
pip install 'at-utility[mcp]'   # or use installed ohm env
export OHM_API_KEY=sk-at-…
export OHM_BASE_URL=https://api.withohm.dev/v1
python tools/docs-context-packer/pack.py https://docs.python.org/3/tutorial/
```

## Skill

See [`skills/docs-context-packer/SKILL.md`](skills/docs-context-packer/SKILL.md).

## License

Same as the Ohm repo (MIT).
