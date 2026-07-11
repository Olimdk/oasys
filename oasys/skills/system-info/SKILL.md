---
description: System information and monitoring. Use when the user wants uptime, disk usage, memory, running processes, current user, or working directory (e.g., "show uptime", "disk usage", "memory summary", "list processes").
---

# System Info

Use the OASYS `sysinfo` plugin or `SHELL:` actions for read-only diagnostics.

## Patterns
- **uptime**: `uptime`
- **df**: `df -h`
- **free**: `free -h`
- **ps**: `ps aux`
- **whoami** / **pwd**

## Notes
Read-only diagnostics. Avoid commands that mutate system state.
