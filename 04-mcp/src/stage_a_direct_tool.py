"""Stage A: direct Python baseline without MCP."""

from direct_tool import add


def run() -> None:
    result = add(2, 3)
    print(f"DIRECT_ADD_2_3={result}")
    assert result == 5
    print("DIRECT_PYTHON_TOOL=PASS")


if __name__ == "__main__":
    run()
