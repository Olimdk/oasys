"""OASYS TUI — Claude Code-style terminal chat interface."""
import re
import time
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Input, Static, RichLog
from textual.containers import Vertical
from rich.markdown import Markdown
from rich.text import Text

from oasys.router import route_completion, route_stream
from oasys.providers import get_provider, available_providers, REGISTRY
from oasys.skills import discover_skills, skills_system_prompt
from oasys.tools import run_shell
from oasys.plugins import discover_plugins
from oasys.files import read_file, write_file
from oasys.session import SessionStats
from oasys import marketplace
from oasys import settings as settings_mod
from oasys import keystore

# Build the markdown code-fence delimiter from chr(96) so this source file
# never literally contains backticks (which would break file-write fences).
BACKTICK = chr(96)
FENCE = BACKTICK * 3

COMMANDS = ["/help", "/skills", "/plugins", "/run", "/model", "/clear", "/compact",
            "/settings", "/key", "/goal", "/overnight", "/stop", "/plugin"]

EDIT_PATTERN = re.compile(r"EDIT:\s*(\S+)\s*\n" + FENCE + r"[a-zA-Z0-9_+-]*\n(.*?)" + FENCE, re.DOTALL)
READ_PATTERN = re.compile(r"^READ:\s*(\S+)\s*$", re.MULTILINE)
SHELL_PATTERN = re.compile(r"^SHELL:\s*(.+)$", re.MULTILINE)


def parse_duration(text: str) -> float:
    """Parse a duration like '5h', '30m', '90m', '1h30m', '45s', '2d', or a
    bare number (interpreted as minutes). Returns seconds (float)."""
    text = text.strip().lower()
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    matches = re.findall(r"(\d+)\s*([smhd])", text)
    if matches:
        return float(sum(int(v) * mult[u] for v, u in matches))
    if text.isdigit():
        return float(int(text) * 60)
    raise ValueError("unparseable duration")


def base_prompt(skills_prompt: str) -> str:
    return (
        "You are OASYS, a local autonomous coding assistant with shell and file access.\n"
        "To run a shell command: SHELL: <command> (one per line, multiple allowed)\n"
        "To read a file: READ: <path>\n"
        "To write/edit a file:\nEDIT: <path>\n" + FENCE + "\n<full new file content>\n" + FENCE + "\n"
        "Only use these when you actually need. " + skills_prompt
    )


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
        self.overnight_active = False
        self.overnight_end = 0.0
        self.overnight_task = None
        self.system_prompt = base_prompt(skills_system_prompt(self.skills))
        self.history = [{"role": "system", "content": self.system_prompt}]
        self.refresh_system_prompt()

    def compose(self) -> ComposeResult:
        yield Vertical(
            RichLog(id="log", wrap=True, highlight=True, markup=True, auto_scroll=True),
            Static("", id="status"),
            Input(placeholder="oasys> (try /help)", id="prompt"),
        )

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[#c15f3c]oasys[/] · {len(self.skills)} skills · {len(self.plugins)} plugins loaded")
        log.write("[#666666]/help for commands · /settings to configure · /goal to set objectives[/]")
        log.write("")
        if not keystore.get_key("OPENROUTER_API_KEY"):
            log.write("[#cc4444]No OPENROUTER_API_KEY set.[/] Run /key openrouter <your-key> or re-run: python -m oasys.setup_wizard")
        goals = settings_mod.get_goals()
        if goals:
            log.write(f"[#666666]{len(goals)} standing goal(s) loaded — they guide /overnight work.[/]")
        self.query_one("#prompt", Input).focus()
        self.update_status()

    def update_status(self) -> None:
        base = self.stats.summary()
        if self.overnight_active and self.overnight_end:
            remaining = max(0, self.overnight_end - time.time())
            hh, rem = divmod(int(remaining), 3600)
            mm, ss = divmod(rem, 60)
            base = f"[#c15f3c]OVERNIGHT {hh:02d}:{mm:02d}:{ss:02d}[/] " + base
        self.query_one("#status", Static).update(base)

    def refresh_system_prompt(self) -> None:
        """Rebuild the system prompt so it reflects current goals, then patch
        the system message at the head of the conversation history."""
        goals = settings_mod.get_goals()
        goal_block = ""
        if goals:
            goal_block = (
                "\n\nSTANDING GOALS (pursue these autonomously when in /overnight mode):\n"
                + "\n".join(f"- {g}" for g in goals)
            )
        self.system_prompt = base_prompt(skills_system_prompt(self.skills)) + goal_block
        if self.history and self.history[0].get("role") == "system":
            self.history[0] = {"role": "system", "content": self.system_prompt}

    # ---------------------------------------------------------------- commands
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
        toks = args.split()
        sub = toks[0] if toks else ""

        if not args.strip() or sub in ("show", "list"):
            return (
                "[#666666]settings:[/]\n" + settings_mod.render(config) +
                "\n\n[#666666]subcommands:[/]\n"
                "[#666666]  /settings set <key> <value>[/]            e.g. max_agent_steps 40, provider openai, voice.output_enabled true\n"
                "[#666666]  /settings get <key>[/]\n"
                "[#666666]  /settings add provider <name> <base_url> [api_key_env] [models...][/]\n"
                "[#666666]  /settings remove provider <name>[/]\n"
                "[#666666]  /settings providers[/]                    list built-in + configured providers"
            )

        if sub == "get" and len(toks) >= 2:
            val = settings_mod.get_key(toks[1], config)
            return f"[#666666]{toks[1]}:[/] {val if val is not None else '[#cc4444](unset)[/]'}"

        if sub == "set" and len(toks) >= 3:
            key, value = toks[1], " ".join(toks[2:])
            new_config = settings_mod.set_key(key, value)
            return f"[#666666]updated:[/] {key} = {value}\n\n" + settings_mod.render(new_config)

        if sub == "providers":
            lines = ["[#666666]configured providers (from config.yaml):[/]"]
            cfg = settings_mod.list_providers()
            if not cfg:
                lines.append("  (none — only built-in providers available)")
            for p in cfg:
                lines.append(f"  [#c15f3c]{p.get('name')}[/]: {p.get('base_url')}  key={p.get('api_key_env')}")
            lines.append("[#666666]built-in providers:[/]")
            for n in REGISTRY.keys():
                lines.append(f"  - {n}")
            return "\n".join(lines)

        if sub == "add" and len(toks) >= 2 and toks[1] == "provider":
            return self._settings_add_provider(toks[2:])

        if sub == "remove" and len(toks) >= 2 and toks[1] == "provider":
            name = toks[2] if len(toks) > 2 else ""
            if not name:
                return "[#cc4444]usage: /settings remove provider <name>[/]"
            ok = settings_mod.remove_provider(name)
            if ok:
                return f"[#666666]removed provider[/] {name}"
            return f"[#cc4444]no such provider:[/] {name}"

        return "[#cc4444]usage: see '/settings' (no args) for subcommands[/]"

    def _settings_add_provider(self, rest: list) -> str:
        if len(rest) < 2:
            return "[#cc4444]usage: /settings add provider <name> <base_url> [api_key_env] [models...][/]"
        name, base_url = rest[0], rest[1]
        api_key_env = rest[2] if len(rest) > 2 else None
        models = []
        if len(rest) > 3:
            for m in rest[3:]:
                models.extend(x for x in m.split(",") if x)
        entry = settings_mod.add_provider(name, base_url, api_key_env, models or None)
        return (
            f"[#666666]added provider[/] {name} -> {base_url}\n"
            f"[#666666]switch to it with:[/] /settings set provider {name}\n"
            f"[#666666]add its API key with:[/] /key {name} <key>"
        )

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

    def handle_goal_command(self, args: str) -> str:
        toks = args.split()
        if not args.strip() or toks[0] == "list":
            goals = settings_mod.get_goals()
            if not goals:
                return "[#666666]no goals set.[/] Use /goal <text> to add one — goals guide autonomous/overnight work."
            return (
                "[#666666]goals:[/]\n" + "\n".join(f"  {i}. {g}" for i, g in enumerate(goals, 1)) +
                "\n\n[#666666]  /goal remove <n>  |  /goal clear[/]"
            )
        if toks[0] == "clear":
            settings_mod.clear_goals()
            self.refresh_system_prompt()
            return "[#666666]cleared all goals[/]"
        if toks[0] == "remove" and len(toks) >= 2 and toks[1].isdigit():
            removed = settings_mod.remove_goal(int(toks[1]))
            self.refresh_system_prompt()
            return f"[#666666]removed goal:[/] {removed}" if removed else "[#cc4444]invalid goal number[/]"
        text = args.strip()
        n = settings_mod.add_goal(text)
        self.refresh_system_prompt()
        return f"[#666666]goal added (#{n}):[/] {text}"

    def handle_overnight_command(self, args: str) -> str:
        if self.overnight_active:
            return "[#cc4444]overnight already running — type /stop to halt[/]"
        if not args.strip():
            return "[#cc4444]usage: /overnight <duration>  e.g. /overnight 5h, /overnight 30m, /overnight 1h30m, /overnight 2d[/]"
        try:
            secs = parse_duration(args.strip())
        except Exception:
            return "[#cc4444]could not parse duration. Use like 5h, 30m, 90m, 1h30m, 2d, or 45 (minutes)[/]"
        if secs <= 0:
            return "[#cc4444]duration must be positive[/]"
        goals = settings_mod.get_goals()
        if not goals:
            return (
                "[#cc4444]no goals set.[/] /overnight works best with a /goal. "
                "Set one first (e.g. /goal refactor the router for clarity). "
                "Re-run /overnight anyway to use generic self-improvement?"
            )
        self.overnight_active = True
        self.overnight_end = time.time() + secs
        self.overnight_task = asyncio.ensure_future(self.run_overnight(secs))
        return (
            f"[#c15f3c]overnight started[/] — autonomous for ~{secs/3600:.2f}h ({(secs//60):.0f} min). "
            f"Type /stop to halt. Goals loaded: {len(goals)}"
        )

    def handle_stop_command(self) -> str:
        if not self.overnight_active:
            return "[#666666]overnight is not running[/]"
        self.overnight_active = False
        return "[#c15f3c]stopping overnight after the current step...[/]"

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
                "[#c15f3c]/settings[/] view/change config (set/get/add provider/remove provider/providers)\n"
                "[#c15f3c]/key <provider> <api_key>[/] save API key (persists to .env)\n"
                "[#c15f3c]/goal <text>[/] set a standing objective (also: /goal list|remove <n>|clear)\n"
                "[#c15f3c]/overnight <duration>[/] run autonomously, e.g. /overnight 5h\n"
                "[#c15f3c]/stop[/] halt an /overnight run\n"
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
        if cmd == "/goal":
            return self.handle_goal_command(args)
        if cmd == "/overnight":
            return self.handle_overnight_command(args)
        if cmd == "/stop":
            return self.handle_stop_command()
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
            return f"[#666666]{len(models)} models available for '{provider.name}', tried in order:[/]\n" + "\n".join(models[:10])
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

        # While overnight mode runs, only /stop is accepted.
        if self.overnight_active:
            if user_text in ("/stop", "stop"):
                self.overnight_active = False
                log.write("[#c15f3c]stop requested — finishing current step...[/]")
            else:
                log.write("[#666666]overnight mode active — type /stop to halt[/]")
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

    def autonomous_prompt(self, iteration: int) -> str:
        goals = settings_mod.get_goals()
        if goals:
            goal_block = "\n".join(f"  - {g}" for g in goals)
        else:
            goal_block = ("  (none set — improve the codebase: fix bugs, add/extend tests, "
                          "improve docs, refactor, add small robustness features)")
        return (
            f"[AUTONOMOUS OVERNIGHT MODE — iteration {iteration}]\n"
            "You are operating with NO human in the loop. Continue the project autonomously.\n"
            f"Standing goal(s):\n{goal_block}\n\n"
            "For this iteration, without asking the user:\n"
            "1. Inspect the repo state (git status/diff, read relevant files) to find the next valuable change.\n"
            "2. Pick ONE focused, safe, verifiable improvement (bug fix, test, refactor, small feature).\n"
            "3. Implement it using SHELL/READ/EDIT. Run the project's tests/linters if present.\n"
            "4. If the change is complete and working, commit it with a clear message (git commit).\n"
            "5. End with a 2-3 sentence summary of what you changed and what to tackle next.\n"
            "Keep each iteration small and working. Do not loop on the same failing change more than "
            "twice; if stuck, move to a different improvement."
        )

    async def run_overnight(self, duration_sec: float) -> None:
        log = self.query_one("#log", RichLog)
        end = time.time() + duration_sec
        self.overnight_end = end
        iteration = 0
        compact_every = max(1, int(settings_mod.load().get("overnight_compact_every", 5) or 5))
        log.write(f"[#c15f3c]=== OVERNIGHT MODE STARTED (~{duration_sec/60:.0f}m) ===[/]")
        try:
            while time.time() < end and self.overnight_active:
                iteration += 1
                remaining = int(end - time.time())
                log.write(f"[#c15f3c]--- overnight iteration {iteration} ({(remaining//60)}m left) ---[/]")
                self.update_status()
                self.history.append({"role": "user", "content": self.autonomous_prompt(iteration)})
                try:
                    await self.run_agent_loop(log)
                except Exception as e:
                    log.write(f"[#cc4444]overnight iteration error:[/] {e}")
                if iteration % compact_every == 0:
                    log.write("[#666666]overnight compaction...[/]")
                    try:
                        await self.do_compact(log)
                    except Exception as e:
                        log.write(f"[#cc4444]compact failed:[/] {e}")
                await asyncio.sleep(0.5)
        finally:
            self.overnight_active = False
            self.overnight_end = 0.0
            log.write("[#c15f3c]=== OVERNIGHT MODE ENDED ===[/]")
            self.update_status()

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


def main() -> None:
    """Console-script entry point (the 'oasys' command)."""
    OasysApp().run()


if __name__ == "__main__":
    main()
