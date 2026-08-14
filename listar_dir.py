from pathlib import Path

# Altere para a raiz do projeto
PROJECT_ROOT = Path(r"M:\REPOs\olist-customer-intelligence")

# Pastas que normalmente não vale a pena listar
IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
}

# Arquivos que normalmente não vale a pena listar
IGNORE_FILES = {
    ".DS_Store",
}

OUTPUT_FILE = "project_structure.txt"


def should_ignore(path: Path) -> bool:
    return (
        any(part in IGNORE_DIRS for part in path.parts)
        or path.name in IGNORE_FILES
    )


def build_tree(root: Path) -> list[str]:
    lines = [f"{root.name}/"]

    def walk(directory: Path, prefix: str = "") -> None:
        entries = sorted(
            (
                entry
                for entry in directory.iterdir()
                if not should_ignore(entry)
            ),
            key=lambda p: (p.is_file(), p.name.lower()),
        )

        for index, entry in enumerate(entries):
            is_last = index == len(entries) - 1

            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                walk(entry, prefix + extension)

    walk(root)

    return lines


def main() -> None:
    if not PROJECT_ROOT.exists():
        raise FileNotFoundError(
            f"Projeto não encontrado: {PROJECT_ROOT}"
        )

    if not PROJECT_ROOT.is_dir():
        raise NotADirectoryError(
            f"O caminho não é uma pasta: {PROJECT_ROOT}"
        )

    tree = build_tree(PROJECT_ROOT)

    output_path = Path(OUTPUT_FILE)
    output_path.write_text(
        "\n".join(tree),
        encoding="utf-8",
    )

    print("\n".join(tree))
    print(f"\nEstrutura salva em: {output_path.resolve()}")


if __name__ == "__main__":
    main()