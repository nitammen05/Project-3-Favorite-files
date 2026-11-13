# Handoff: Project 3, Favorite Files

Last updated: 2026-11-13

## Status: done and working

The program described in `Spec.md` is built, tested (31 tests, all passing), and
committed (`a5236af`). Nothing is half-finished.

## Files

| File | What it is |
|---|---|
| `Problem.md`, `Spec.md`, `CLAUDE.md` | Originals written by the user. Do not edit or delete. |
| `Test-files/` | Sample files (`.py`, `.txt`, `.jpg`). Do not edit or delete. |
| `favorites.py` | The program. |
| `test_favorites.py` | Tests, using Python's built-in `unittest` (pytest is not installed). |
| `.gitignore` | Keeps `__pycache__/` and `.DS_Store` out of git. |

## How to run

```bash
cd ~/csc299-main/Project-3-Favorite-files
python3 favorites.py add Test-files/*     # add files
python3 favorites.py list                 # show the favorites tree
python3 favorites.py                      # interactive mode ('list', 'quit')
python3 -m unittest -v                    # run the tests
```

Add `--dir PATH` before the command to use a folder other than `~/favorites`.

## How it works (functions in favorites.py)

- `get_category`: picks a folder from the extension (`.txt` to `text`, `.py` to
  `code`, `.jpg` to `images`, unknown to `other`). The `CATEGORIES` dict holds the list.
- `create_favorites_folder`: makes `~/favorites` if it doesn't exist.
- `unique_destination`: avoids overwriting (`notes.txt` becomes `notes_1.txt`, ...).
- `add_file`: **copies** the file into `favorites/<category>/`.
- `path_visual` / `tree_visual`: draw the `└──` diagrams.
- `clean_input_path`: tidies typed or dragged-in paths (quotes, `\ ` spaces).
- `add_and_report`, `interactive`, `main`: the terminal interface.

## Decisions made (and why)

- **Copy, not move.** Moving would remove the original, which breaks the CLAUDE.md
  rule "do not edit or delete original files."
- **Default location `~/favorites`**, with an option (`--dir`) to put it elsewhere,
  so the tests never touch the real folder.
- **Sort by extension.** This is simple and predictable; reading file contents
  wasn't needed for the spec.

## For the next session (tutoring)

- The user has run the program and asked how to run the tests. Their comfort with the
  command line (paths, `cd`) has not been confirmed yet. Ask about it.
- Open check-your-understanding questions to revisit:
  1. What happens when the same file is added twice? (It is saved as `Hello-World_1.txt`.)
  2. Where does `song.MP3` go, and why? (`audio`, because of `.lower()` in `get_category`.)
  3. Break a test on purpose (change `"other"` to `"text"` in
     `test_unknown_extension`) and predict the result.

## Possible next steps (only if the user wants them)

- A `remove` command, or opening the favorites folder in Finder from the program.
- More file types in `CATEGORIES`.
