import argparse
import json

from app.container import get_container


def run_once(message: str, show_tools: bool) -> int:
    result = get_container().agent.run(message)
    print("\nAssistant:\n")
    print(result.answer)

    if show_tools:
        print("\nTool Trace:\n")
        print(json.dumps(result.tool_trace, indent=2))
    return 0


def interactive_loop(show_tools: bool) -> int:
    print("Retail AI Assistant CLI")
    print("Type 'exit' to quit.\n")
    while True:
        message = input("You: ").strip()
        if not message:
            continue
        if message.lower() in {"exit", "quit"}:
            return 0
        run_once(message, show_tools=show_tools)
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="CLI entrypoint for the Retail AI Assistant.")
    parser.add_argument("message", nargs="?", help="Optional single message to send to the assistant.")
    parser.add_argument(
        "--show-tools",
        action="store_true",
        help="Print tool call arguments and results after the answer.",
    )
    args = parser.parse_args()

    if args.message:
        return run_once(args.message, show_tools=args.show_tools)
    return interactive_loop(show_tools=args.show_tools)


if __name__ == "__main__":
    raise SystemExit(main())
