# ~/.claude

Personal [Claude Code](https://claude.ai/code) configuration, stored at `~/.claude`.

## Tracked files

```
~/.claude/
├── .claude/CLAUDE.md                    # Project-level instructions for Claude (repo-scoped, not global)
├── settings.json                        # Claude Code settings (hooks, plugins, theme, voice, status line)
├── .gitignore                           # Excludes runtime data, sessions, cache, plugins, most skills
└── skills/
    ├── relationship-liangsirui/         # 梁斯睿 — created with dot-skill
    ├── relationship-wangziqian/         # 王紫倩 — created with dot-skill
    └── relationship-zhoushiyun/        # 周诗韵 — created with dot-skill
```

Relationship skills are generated using [dot-skill / colleague-skill](https://github.com/titanwings/colleague-skill).

Runtime directories (`sessions/`, `cache/`, `plugins/`, `projects/`, etc.) are gitignored and managed locally by Claude Code. Most skills are also gitignored; only the relationship skills above are tracked.

## Notes

- MCP server configs (user/local scope) live in `~/.claude.json`, not here
- Project-scoped MCP servers use `.mcp.json` in the project root
- Skills are installed locally under `skills/` but not tracked in this repo
