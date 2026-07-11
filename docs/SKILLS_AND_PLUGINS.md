# Installing Skills and Plugins in OASYS

## Skills (Claude Code-compatible)

OASYS automatically reads any skill from two locations, checked in this order:

1. ~/.claude/skills/ - if you already use Claude Code and have skills installed there, OASYS picks them up automatically. No copying needed.
2. oasys/skills/ - OASYS-local skills, for ones you do not want shared with Claude Code.

A skill is just a folder containing a SKILL.md file, e.g. ~/.claude/skills/my-skill/SKILL.md

## Plugins (OASYS-specific)

A plugin is a single Python file in oasys/plugins/ exposing a NAME string, a DESCRIPTION string, and a run(args, ctx) function that returns a string shown in the TUI.

Drop the file in oasys/plugins/, restart OASYS, and it shows up in /plugins.
Run it with: /run <plugin-name> <args>

## Marketplaces (install from GitHub)

Commands:
  /plugin marketplace add <owner/repo>
  /plugin marketplace list
  /plugin install <item-name>@<marketplace-alias>

Example:
  /plugin marketplace add jeffallan/claude-skills
  /plugin marketplace list
  /plugin install fullstack-dev-skills@claude-skills-jeffallan

The marketplace alias is <repo-name>-<owner>. Check the exact alias printed after
marketplace add before running install.
