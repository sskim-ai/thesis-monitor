import os
import secrets
from pathlib import Path
from tempfile import NamedTemporaryFile


def main() -> None:
    path = Path(".env")
    lines = path.read_text(encoding="utf-8").splitlines()
    generated = secrets.token_urlsafe(32)
    found = False
    changed = False
    updated: list[str] = []
    for line in lines:
        if line.startswith("ACTION_API_KEY="):
            found = True
            if line == "ACTION_API_KEY=":
                updated.append(f"ACTION_API_KEY={generated}")
                changed = True
            else:
                updated.append(line)
        else:
            updated.append(line)
    if not found:
        updated.append(f"ACTION_API_KEY={generated}")
        changed = True
    if not changed:
        print("ACTION_API_KEY is already configured")
        return
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write("\n".join(updated) + "\n")
        temporary_path = Path(handle.name)
    os.chmod(temporary_path, 0o600)
    os.replace(temporary_path, path)
    print("ACTION_API_KEY was generated and stored in .env")


if __name__ == "__main__":
    main()
