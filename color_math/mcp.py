"""Direct module entrypoint for running the Color Math MCP server: python -m color_math.mcp"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="color-math-mcp",
        description="Run the Python Color Math Model Context Protocol (MCP) server.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE or HTTP transport (default: 8000)",
    )
    args = parser.parse_args()

    try:
        from .mcp_server import run_mcp_server
    except ImportError as e:
        print(f"Error starting Color Math MCP server:\n{e}", file=sys.stderr)
        sys.exit(1)

    extra_kwargs = {}
    if args.transport in {"sse", "streamable-http"}:
        extra_kwargs["port"] = args.port

    run_mcp_server(transport=args.transport, **extra_kwargs)


if __name__ == "__main__":
    main()
