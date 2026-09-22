"""Removed subprocess orchestrator. Use native Codex subagents instead."""
import sys

def main():
    print("The CLI-driven research loop was retired. In Codex, invoke $research-autopilot. "
          "checkpoint.py only records native-session progress; it never starts a model.", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
