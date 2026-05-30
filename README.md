# ~/.claude

Personal [Claude Code](https://claude.ai/code) configuration, stored at `~/.claude`.

## Tracked files

```
~/.claude/
├── settings.json       # Claude Code settings (hooks, plugins, theme, voice, status line)
└── .gitignore          # Excludes runtime data, sessions, cache, plugins, skills
```

Runtime directories (`sessions/`, `cache/`, `plugins/`, `skills/`, `projects/`, etc.) are gitignored and managed locally by Claude Code.

## Notes

- MCP server configs (user/local scope) live in `~/.claude.json`, not here
- Project-scoped MCP servers use `.mcp.json` in the project root
- Skills are installed locally under `skills/` but not tracked in this repo
