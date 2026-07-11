"""Example plugin: reports basic system info."""
import platform

NAME = "sysinfo"
DESCRIPTION = "Show OS, Python version, and machine info"


def run(args: str, ctx: dict) -> str:
    return (
        f"OS: {platform.system()} {platform.release()}\n"
        f"Python: {platform.python_version()}\n"
        f"Machine: {platform.machine()}"
    )
