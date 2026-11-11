"""Tests for favorites.py. Run with:  python3 -m unittest -v"""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import favorites


class TestGetCategory(unittest.TestCase):
    def test_text_file(self):
        self.assertEqual(favorites.get_category("notes.txt"), "text")

    def test_python_file_is_code(self):
        self.assertEqual(favorites.get_category("Hello-World.py"), "code")

    def test_image(self):
        self.assertEqual(favorites.get_category("image.jpg"), "images")

    def test_uppercase_extension(self):
        self.assertEqual(favorites.get_category("PHOTO.JPG"), "images")

    def test_unknown_extension(self):
        self.assertEqual(favorites.get_category("mystery.xyz"), "other")

    def test_no_extension(self):
        self.assertEqual(favorites.get_category("Makefile"), "other")

    def test_full_path(self):
        self.assertEqual(favorites.get_category("/some/folder/report.pdf"), "documents")


class TempDirTestCase(unittest.TestCase):
    """Gives each test its own empty temporary folder, deleted afterwards."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.fav = self.tmp / "favorites"

    def tearDown(self):
        self._tmp.cleanup()

    def make_file(self, name, content="hello"):
        path = self.tmp / name
        path.write_text(content)
        return path


class TestCreateFavoritesFolder(TempDirTestCase):
    def test_creates_folder(self):
        result = favorites.create_favorites_folder(self.fav)
        self.assertTrue(self.fav.is_dir())
        self.assertEqual(result, self.fav)

    def test_existing_folder_is_fine(self):
        favorites.create_favorites_folder(self.fav)
        favorites.create_favorites_folder(self.fav)  # no error the second time
        self.assertTrue(self.fav.is_dir())


class TestUniqueDestination(TempDirTestCase):
    def test_free_name(self):
        self.assertEqual(favorites.unique_destination(self.tmp, "a.txt"), self.tmp / "a.txt")

    def test_taken_name_gets_number(self):
        self.make_file("a.txt")
        self.make_file("a_1.txt")
        self.assertEqual(favorites.unique_destination(self.tmp, "a.txt"), self.tmp / "a_2.txt")


class TestAddFile(TempDirTestCase):
    def test_text_file_goes_to_text_folder(self):
        source = self.make_file("notes.txt", "my notes")
        result = favorites.add_file(source, self.fav)
        self.assertEqual(result, self.fav / "text" / "notes.txt")
        self.assertEqual(result.read_text(), "my notes")

    def test_original_is_untouched(self):
        source = self.make_file("notes.txt", "my notes")
        favorites.add_file(source, self.fav)
        self.assertTrue(source.exists())
        self.assertEqual(source.read_text(), "my notes")

    def test_creates_favorites_folder_if_missing(self):
        self.assertFalse(self.fav.exists())
        favorites.add_file(self.make_file("x.py"), self.fav)
        self.assertTrue((self.fav / "code" / "x.py").is_file())

    def test_adding_same_name_twice_keeps_both(self):
        first = favorites.add_file(self.make_file("notes.txt", "one"), self.fav)
        second = favorites.add_file(self.make_file("notes.txt", "two"), self.fav)
        self.assertEqual(first.read_text(), "one")
        self.assertEqual(second.name, "notes_1.txt")
        self.assertEqual(second.read_text(), "two")

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            favorites.add_file(self.tmp / "nope.txt", self.fav)

    def test_folder_is_not_a_file(self):
        with self.assertRaises(FileNotFoundError):
            favorites.add_file(self.tmp, self.fav)


class TestPathVisual(TempDirTestCase):
    def test_draws_route_to_file(self):
        result = favorites.path_visual(self.fav / "text" / "notes.txt", self.fav)
        expected = "favorites/\n└── text/\n    └── notes.txt"
        self.assertEqual(result, expected)


class TestTreeVisual(TempDirTestCase):
    def test_missing_folder(self):
        self.assertIn("empty", favorites.tree_visual(self.fav))

    def test_draws_whole_tree(self):
        favorites.add_file(self.make_file("b.txt"), self.fav)
        favorites.add_file(self.make_file("a.txt"), self.fav)
        favorites.add_file(self.make_file("x.py"), self.fav)
        expected = "\n".join([
            "favorites/",
            "├── code/",
            "│   └── x.py",
            "└── text/",
            "    ├── a.txt",
            "    └── b.txt",
        ])
        self.assertEqual(favorites.tree_visual(self.fav), expected)

    def test_hidden_files_skipped(self):
        favorites.create_favorites_folder(self.fav)
        (self.fav / ".DS_Store").write_text("")
        self.assertNotIn(".DS_Store", favorites.tree_visual(self.fav))


class TestCleanInputPath(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(favorites.clean_input_path("  a.txt \n"), "a.txt")

    def test_quotes(self):
        self.assertEqual(favorites.clean_input_path("'My File.txt'"), "My File.txt")
        self.assertEqual(favorites.clean_input_path('"My File.txt"'), "My File.txt")

    def test_dragged_in_spaces(self):
        self.assertEqual(favorites.clean_input_path("My\\ File.txt"), "My File.txt")


class TestAddAndReport(TempDirTestCase):
    def test_success_message(self):
        message = favorites.add_and_report(self.make_file("a.txt"), self.fav)
        self.assertIn(str(self.fav / "text" / "a.txt"), message)
        self.assertIn("└── a.txt", message)

    def test_error_message(self):
        message = favorites.add_and_report(self.tmp / "nope.txt", self.fav)
        self.assertTrue(message.startswith("Error"))


def run(func, *args, **kwargs):
    """Call func and return (its result, everything it printed)."""
    out = io.StringIO()
    with redirect_stdout(out):
        result = func(*args, **kwargs)
    return result, out.getvalue()


class TestInteractive(TempDirTestCase):
    def test_add_list_quit(self):
        source = self.make_file("song.mp3")
        typed = iter([str(source), "list", "", "quit"])
        _, output = run(favorites.interactive, self.fav, input_func=lambda _: next(typed))
        self.assertTrue((self.fav / "audio" / "song.mp3").is_file())
        self.assertIn("audio/", output)
        self.assertIn("Goodbye", output)

    def test_end_of_input_exits(self):
        def no_more_input(_):
            raise EOFError
        _, output = run(favorites.interactive, self.fav, input_func=no_more_input)
        self.assertIn("Goodbye", output)


class TestMain(TempDirTestCase):
    def test_add_command(self):
        a, b = self.make_file("a.txt"), self.make_file("b.py")
        code, output = run(favorites.main, ["--dir", str(self.fav), "add", str(a), str(b)])
        self.assertEqual(code, 0)
        self.assertTrue((self.fav / "text" / "a.txt").is_file())
        self.assertTrue((self.fav / "code" / "b.py").is_file())
        self.assertEqual(output.count("Added!"), 2)

    def test_add_missing_file_returns_1(self):
        code, output = run(favorites.main, ["--dir", str(self.fav), "add", "nope.txt"])
        self.assertEqual(code, 1)
        self.assertIn("Error", output)

    def test_list_command(self):
        favorites.add_file(self.make_file("a.txt"), self.fav)
        code, output = run(favorites.main, ["--dir", str(self.fav), "list"])
        self.assertEqual(code, 0)
        self.assertIn("a.txt", output)


if __name__ == "__main__":
    unittest.main()
