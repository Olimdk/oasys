"""OASYS TUI — Claude Code-style terminal chat interface."""
import re
import time
from textual.app import App, ComposeResult
from textual.widgets import Input, Static, RichLog
from textual.containers import Vertical
from rich.markdown import Markdown
from rich.text import Text

from oasys.router import route_completion, route_stream
from oasys.providers import get_provider
from oasys.skills import discover_skills, skills_system_prompt
from oasys.tools import run_shell
from oasys.plugins import discover_plugins
from oasys.files import read_file, write_file
from oasys.session import SessionStats
from oasys import marketplace
from oasys import settings as settings_mod
from oasys import keystore

COMMANDS = ["/help", "/skills", "/plugins", "/run", "/model", "/clear", "/compact", "/plugin", "/settings", "/key"]

EDIT_PATTERN = re.compile(r"EDIT:\s*(\S+)\s*\n```[a-zA-Z0-9_+-]*\n(.*?)```", re.DOTALL)
READ_PATTERN = re.compile(r"^READ:\s*(\S+)\s*$", re.MULTILINE)
SHELL_PATTERN = re.compile(r"^SHELL:\s*(.+)$", re.MULTILINE)


class OasysApp(App):
    CSS = """
    Screen { background: #0c0c0c; }
    RichLog { background: #0c0c0c; border: none; padding: 1 2; scrollbar-size: 1 1; }
    #status { background: #0c0c0c; color: #444444; padding: 0 2; height: 1; }
    Input {
        background: #0c0c0c; border: none; border-top: solid #2a2a2a;
        padding: 0 2; color: #e0e0e0;
    }
    Input:focus { border-top: solid #c15f3c; }
    """
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.skills = discover_skills()
        self.plugins = discover_plugins()
        self.stats = SessionStats()
        self.system_prompt = (
            "You are OASYS, a local autonomous coding assistant with shell and file access.\n"
            "To run a shell command: SHELL: <command> (one per line, multiple allowed)\n"
            "To read a file: READ: <path>\n"
            "To write/edit a file:\nEDIT: <path>\n```\n<full new file content>\n```\n"
            "Only use these when you actually need to. " + skills_system_prompt(self.skills)
        )
        self.history = [{"role": "system", "content": self.system_prompt}]

    def compose(self) -> ComposeResult:
        yield Vertical(
            RichLog(id="log", wrap=True, highlight=True, markup=True, auto_scroll=True),
            Static("", id="status"),
            Input(placeholder="oasys> (try /help)", id="prompt"),
        )

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[#c15f3c]oasys[/] · {len(self.skills)} skills · {len(self.plugins)} plugins loaded")
        log.write("[#666666]/help for commands · /settings to configure[/]")
        log.write("")
        if not keystore.get_key("OPENROUTER_API_KEY"):
            log.write("[#cc4444]No OPENROUTER_API_KEY set.[/] Run /key openrouter <your-key> or re-run: python -m oasys.setup_wizard")
        self.query_one("#prompt", Input).focus()
        self.update_status()

    def update_status(self) -> None:
        self.query_one("#status", Static).update(self.stats.summary())

    def handle_plugin_command(self, args: str) -> str:
        parts = args.split(maxsplit=2)
        if not parts:
            return "[#cc4444]usage: /plugin marketplace add <owner/repo> | /plugin install <name>@<alias> | /plugin marketplace list[/]"
        if parts[0] == "marketplace" and len(parts) >= 2:
            if parts[1] == "add" and len(parts) == 3:
                return marketplace.marketplace_add(parts[2])
            if parts[1] == "list":
                return marketplace.marketplace_list()
        if parts[0] == "install" and len(parts) == 2:
            result = marketplace.install(parts[1])
            self.skills = discover_skills()
            self.plugins = discover_plugins()
            return result
        return "[#cc4444]usage: /plugin marketplace add <owner/repo> | /plugin install <name>@<alias> | /plugin marketplace list[/]"

    def handle_settings_command(self, args: str) -> str:
        config = settings_mod.load()
        if not args:
            return "[#666666]current settings:[/]\n" + settings_mod.render(config) + \
                   "\n\n[#666666]change with: /settings set <key> <value>[/]\n" \
                   "[#666666]e.g. /settings set max_agent_steps 40[/]\n" \
                   "[#666666]e.g. /settings set voice.output_enabled true[/]\n" \
                   "[#666666]e.g. /settings set provider openrouter[/]"
        parts = args.split(maxsplit=2)
        if parts[0] == "set" and len(parts) == 3:
            _, key, value = parts
            new_config = settings_mod.set_key(key, value)
            return f"[#666666]updated:[/] {key} = {value}\n\n" + settings_mod.render(new_config)
        return "[#cc4444]usage: /settings  |  /settings set <key> <value>[/]"
    def handle_key_command(self, args: str) -> str:
        if not args.strip() or args.strip() == "status":
            st = keystore.key_status()
            lines = [f"[#666666]{k}:[/] {v if v else '[#cc4444]not set[/]'}" for k, v in st.items()]
            return (
                "[#666666]API key status:[/]\n"
                + "\n".join(lines)
                + "\n\n[#666666]set a key with: /key <provider> <key>[/]\n"
                + "[#666666]e.g. /key openrouter sk-or-...[/]"
            )
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            return "[#cc4444]usage: /key <provider> <api_key>  |  /key status[/]"
        provider, api_key = parts[0], parts[1].strip()
        env_var = f"{provider.upper()}_API_KEY"
        keystore.set_key(env_var, api_key)
        return f"[#666666]saved[/] {env_var} -> .env (persisted across restarts)."

    def handle_command(self, cmd: str, args: str) -> str | None:
        if cmd == "/help":
            return (
                "[#c15f3c]/help[/] this menu\n"
                "[#c15f3c]/skills[/] list loaded skills\n"
                "[#c15f3c]/plugins[/] list loaded plugins\n"
                "[#c15f3c]/run <plugin> [args][/] execute a plugin\n"
                "[#c15f3c]/model[/] show current model list\n"
                "[#c15f3c]/clear[/] reset conversation history\n"
                "[#c15f3c]/compact[/] summarize history to save context\n"
                "[#c15f3c]/settings[/] view/change config (steps, voice, provider)\n"
                "[#c15f3c]/key <provider> <api_key>[/] save API key (persists to .env)\n"
                "[#c15f3c]/plugin marketplace add <owner/repo>[/] add a marketplace\n"
                "[#c15f3c]/plugin install <name>@<alias>[/] install a skill/plugin\n"
                "[#c15f3c]/plugin marketplace list[/] show added marketplaces"
            )
        if cmd == "/skills":
            if not self.skills:
                return "[#666666]No skills found in oasys/skills[/]"
            return "\n".join(f"[#c15f3c]{s.name}[/] — {s.description or '(no description)'}" for s in self.skills)
        if cmd == "/plugins":
            if not self.plugins:
                return "[#666666]No plugins found in oasys/plugins[/]"
            return "\n".join(f"[#c15f3c]{p.name}[/] — {p.description}" for p in self.plugins.values())
        if cmd == "/plugin":
            return self.handle_plugin_command(args)
        if cmd == "/settings":
            return self.handle_settings_command(args)
        if cmd == "/key":
            return self.handle_key_command(args)
        if cmd == "/run":
            parts = args.split(maxsplit=1)
            if not parts:
                return "[#cc4444]usage: /run <plugin> [args][/]"
            pname, pargs = parts[0], parts[1] if len(parts) > 1 else ""
            plugin = self.plugins.get(pname)
            if not plugin:
                return f"[#cc4444]no such plugin: {pname}[/]"
            try:
                return plugin.run(pargs, {"history": self.history})
            except Exception as e:
                return f"[#cc4444]plugin error:[/] {e}"
        if cmd == "/model":
            config = settings_mod.load()
            provider = get_provider(config.get("provider", "openrouter"))
            models = provider.free_models()
            return f"[#666666]{len(models)} free models available, tried in order:[/]\n" + "\n".join(models[:10])
        if cmd == "/clear":
            self.history = [{"role": "system", "content": self.system_prompt}]
            return "[#666666]conversation cleared[/]"
        return f"[#cc4444]unknown command: {cmd}[/] (try /help)"

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        log = self.query_one("#log", RichLog)
        prompt_box = self.query_one("#prompt", Input)
        user_text = event.value.strip()
        prompt_box.value = ""
        if not user_text:
            return

        log.write(f"[#888888]>[/] {user_text}")

        if user_text.startswith("/"):
            parts = user_text.split(maxsplit=1)
            cmd, args = parts[0], parts[1] if len(parts) > 1 else ""
            if cmd == "/compact":
                await self.do_compact(log)
            else:
                result = self.handle_command(cmd, args)
                if result:
                    log.write(result)
                log.write("")
            return

        self.history.append({"role": "user", "content": user_text})
        await self.run_agent_loop(log)

    async def do_compact(self, log: RichLog) -> None:
        log.write("[#666666]compacting conversation...[/]")
        summary_request = self.history + [{
            "role": "user",
            "content": "Summarize this conversation in a few dense paragraphs, preserving "
                       "decisions, file paths, and context. This replaces the full history."
        }]
        try:
            data = await route_completion(summary_request)
            summary = data["choices"][0]["message"]["content"]
        except Exception as e:
            log.write(f"[#cc4444]compact failed:[/] {e}")
            log.write("")
            return
        self.history = [
            {"role": "system", "content": self.system_prompt},
            {"role": "assistant", "content": f"[Earlier conversation summary]\n{summary}"},
        ]
        log.write("[#666666]conversation compacted[/]")
        log.write("")

    def extract_actions(self, reply: str):
        actions = []
        for m in EDIT_PATTERN.finditer(reply):
            actions.append(("edit", m.group(1).strip(), m.group(2)))
        remaining = EDIT_PATTERN.sub("", reply)
        for m in READ_PATTERN.finditer(remaining):
            actions.append(("read", m.group(1).strip(), None))
        remaining = READ_PATTERN.sub("", remaining)
        for m in SHELL_PATTERN.finditer(remaining):
            actions.append(("shell", m.group(1).strip(), None))
        remaining = SHELL_PATTERN.sub("", remaining)
        return remaining.strip(), actions

    async def run_agent_loop(self, log: RichLog) -> None:
        config = settings_mod.load()
        max_steps = config.get("max_agent_steps", 25)

        for step in range(max_steps):
            start = time.perf_counter()
            model_used = "?"
            full_text = ""
            usage = {}

            try:
                async for chunk, done, u, model in route_stream(self.history):
                    model_used = model
                    if chunk:
                        full_text += chunk
                    if u:
                        usage = u
                    if done:
                        break
            except Exception as e:
                log.write(f"[#cc4444]error:[/] {e}")
                log.write("")
                return

            elapsed = time.perf_counter() - start
            self.stats.record(usage)
            self.update_status()

            self.history.append({"role": "assistant", "content": full_text})
            display_text, actions = self.extract_actions(full_text)

            if display_text:
                log.write(f"[#c15f3c]oasys[/] [#666666]({model_used})[/]")
                log.write(Markdown(display_text))

            if not actions:
                tok = usage.get("total_tokens", "?")
                log.write(f"[#444444]{elapsed:.1f}s · {tok} tokens[/]")
                log.write("")
                return

            outputs = []
            for kind, target, content in actions:
                if kind == "shell":
                    log.write(f"[#c15f3c]$[/] {target}")
                    out = await run_shell(target)
                    log.write(f"[#666666]{out}[/]")
                    outputs.append(f"$ {target}\n{out}")
                elif kind == "read":
                    log.write(f"[#c15f3c]read[/] {target}")
                    out = read_file(target)
                    preview = out if len(out) < 2000 else out[:2000] + "\n...[truncated]"
                    log.write(f"[#666666]{preview}[/]")
                    outputs.append(f"[read {target}]\n{out}")
                elif kind == "edit":
                    diff, msg = write_file(target, content)
                    log.write(f"[#c15f3c]edit[/] {target}")
                    log.write(Text(diff, style="#888888"))
                    log.write(f"[#666666]{msg}[/]")
                    outputs.append(f"[edit {target}]\n{msg}")

            tok = usage.get("total_tokens", "?")
            log.write(f"[#444444]{elapsed:.1f}s · {tok} tokens[/]")
            self.history.append({"role": "user", "content": "[action results]\n" + "\n\n".join(outputs)})

        log.write(f"[#cc4444]stopped: hit {max_steps}-step limit for this turn (change with /settings set max_agent_steps N)[/]")
        log.write("")


if __name__ == "__main__":
    OasysApp().run()
