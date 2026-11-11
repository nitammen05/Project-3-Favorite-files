"""favorites.py - keep copies of your favorite files in one sorted folder.

Usage (from a terminal):
    python3 favorites.py add FILE [FILE ...]   copy files into favorites, sorted
    python3 favorites.py list                  show everything in favorites
    python3 favorites.py                       interactive mode (type file paths)

Add --dir PATH (before the command) to use a folder other than ~/favorites.
Original files are never changed or deleted; the program makes copies.
"""

import argparse
import shutil
from pathlib import Path

DEFAULT_DIR = Path.home() / "favorites"

# Which folder each file extension belongs in. Extensions are lowercase.
CATEGORIES = {
    "text": [".txt", ".md", ".rtf", ".log"],
    "code": [".py", ".js", ".java", ".c", ".cpp", ".h", ".html", ".css",
             ".sh", ".rb", ".go", ".rs", ".ts", ".json", ".r"],
    "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
               ".heic", ".tiff"],
    "audio": [".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"],
    "video": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "documents": [".pdf", ".doc", ".docx", ".odt", ".pages"],
    "spreadsheets": [".xls", ".xlsx", ".csv", ".numbers", ".ods"],
    "presentations": [".ppt", ".pptx", ".key", ".odp"],
    "archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
}
OTHER = "other"


def get_category(file_path):
    """Return the name of the folder a file belongs in, based on its extension."""
    extension = Path(file_path).suffix.lower()
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
    return OTHER


def create_favorites_folder(favorites_dir=DEFAULT_DIR):
    """Make the favorites folder if it does not exist yet. Return its path."""
    favorites_dir = Path(favorites_dir).expanduser()
    favorites_dir.mkdir(parents=True, exist_ok=True)
    return favorites_dir


def unique_destination(folder, file_name):
    """Return a path in folder for file_name that is not already taken.

    notes.txt -> notes.txt, or notes_1.txt, notes_2.txt, ... if taken.
    """
    destination = Path(folder) / file_name
    stem, suffix = destination.stem, destination.suffix
    number = 1
    while destination.exists():
        destination = Path(folder) / f"{stem}_{number}{suffix}"
        number += 1
    return destination


def add_file(file_path, favorites_dir=DEFAULT_DIR):
    """Copy a file into the right category folder. Return the new file's path.

    The original file is left exactly as it was.
    Raises FileNotFoundError if file_path is not an existing file.
    """
    source = Path(file_path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"No such file: {file_path}")
    favorites_dir = create_favorites_folder(favorites_dir)
    category_folder = favorites_dir / get_category(source)
    category_folder.mkdir(exist_ok=True)
    destination = unique_destination(category_folder, source.name)
    shutil.copy2(source, destination)  # copy2 also keeps the file's dates
    return destination


def path_visual(file_path, favorites_dir=DEFAULT_DIR):
    """Draw the route from the favorites folder down to one file, e.g.

    favorites/
    └── text/
        └── notes.txt
    """
    favorites_dir = Path(favorites_dir).expanduser()
    parts = Path(file_path).relative_to(favorites_dir).parts
    lines = [favorites_dir.name + "/"]
    for depth, part in enumerate(parts):
        is_last = depth == len(parts) - 1
        name = part if is_last else part + "/"
        lines.append("    " * depth + "└── " + name)
    return "\n".join(lines)


def tree_visual(favorites_dir=DEFAULT_DIR):
    """Draw everything inside the favorites folder as a tree."""
    favorites_dir = Path(favorites_dir).expanduser()
    if not favorites_dir.is_dir():
        return f"{favorites_dir.name}/  (empty - no files added yet)"
    lines = [favorites_dir.name + "/"]

    def walk(folder, prefix):
        # Hidden files like .DS_Store are skipped; folders are listed first.
        entries = sorted(
            (e for e in folder.iterdir() if not e.name.startswith(".")),
            key=lambda e: (not e.is_dir(), e.name.lower()),
        )
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            branch = "└── " if is_last else "├── "
            lines.append(prefix + branch + entry.name + ("/" if entry.is_dir() else ""))
            if entry.is_dir():
                walk(entry, prefix + ("    " if is_last else "│   "))

    walk(favorites_dir, "")
    return "\n".join(lines)


def clean_input_path(text):
    """Tidy a path the user typed or dragged into the terminal.

    Removes surrounding spaces and quotes, and turns "My\\ File.txt"
    (how macOS writes spaces when you drag a file in) into "My File.txt".
    """
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    return text.replace("\\ ", " ")


def add_and_report(file_path, favorites_dir=DEFAULT_DIR):
    """Add one file and return the message to show the user."""
    try:
        destination = add_file(file_path, favorites_dir)
    except FileNotFoundError as error:
        return f"Error: {error}"
    return (f"Added! Your file is saved at:\n  {destination}\n\n"
            + path_visual(destination, favorites_dir))


def interactive(favorites_dir=DEFAULT_DIR, input_func=input):
    """Keep asking for files to add until the user types 'quit'."""
    folder = create_favorites_folder(favorites_dir)
    print(f"Favorites folder: {folder}")
    print("Type (or drag in) a file path to add it.")
    print("Commands: 'list' shows all favorites, 'quit' exits.\n")
    while True:
        try:
            text = clean_input_path(input_func("file> "))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in ("quit", "exit", "q"):
            break
        if text.lower() == "list":
            print(tree_visual(favorites_dir))
        elif text:
            print(add_and_report(text, favorites_dir))
        print()
    print("Goodbye!")


def main(argv=None):
    """Read the command line and run the matching command. Return exit code."""
    parser = argparse.ArgumentParser(
        description="Copy your favorite files into one folder, sorted by type.")
    parser.add_argument("--dir", default=DEFAULT_DIR,
                        help="where the favorites folder lives (default: ~/favorites)")
    commands = parser.add_subparsers(dest="command")
    add_parser = commands.add_parser("add", help="add one or more files")
    add_parser.add_argument("files", nargs="+", help="files to add")
    commands.add_parser("list", help="show everything in favorites")
    args = parser.parse_args(argv)

    if args.command == "add":
        exit_code = 0
        for file_path in args.files:
            message = add_and_report(file_path, args.dir)
            print(message + "\n")
            if message.startswith("Error"):
                exit_code = 1
        return exit_code
    if args.command == "list":
        print(tree_visual(args.dir))
        return 0
    interactive(args.dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
