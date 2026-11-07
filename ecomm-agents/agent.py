"""Backward-compatible command-line entry point for the shopping assistant."""

from smart_shopping_agent import main, run_shopping_request

__all__ = ["main", "run_shopping_request"]


if __name__ == "__main__":
    main()
