import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


class ScrollSc2ViewerInputExpansionTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.base_dir = Path(cls._tmpdir.name)
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.input_dir = cls.base_dir / "inputs"
        cls.input_dir.mkdir(parents=True, exist_ok=True)
        cls.dummy_arg = cls.base_dir / "dummy.png"
        cls.dummy_arg.write_bytes(b"")

        (cls.input_dir / "b.PNG").write_bytes(b"")
        (cls.input_dir / "a.png").write_bytes(b"")
        (cls.input_dir / "ignore.jpg").write_bytes(b"")
        subdir = cls.input_dir / "subdir"
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / "c.png").write_bytes(b"")

        cls.extra_file = cls.base_dir / "extra.png"
        cls.extra_file.write_bytes(b"")

        cls._original_argv = sys.argv[:]
        sys.argv = ["scroll_sc2_viewer_megarom", "-i", str(cls.dummy_arg)]
        module_path = cls.repo_root / "projects" / "sc2_viewer_rom" / "src" / "scroll_sc2_viewer_megarom.py"
        spec = importlib.util.spec_from_file_location(
            "scroll_sc2_viewer_megarom", module_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Failed to load scroll_sc2_viewer_megarom module spec.")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        sys.argv = cls._original_argv
        cls._tmpdir.cleanup()

    def test_list_pngs_in_dir(self):
        pngs = self.module.list_pngs_in_dir(self.input_dir)
        self.assertEqual([p.name for p in pngs], ["a.png", "b.PNG"])

    def test_expand_input_group(self):
        expanded = self.module.expand_input_group([self.input_dir, self.extra_file])
        self.assertEqual(
            [p.name for p in expanded],
            ["a.png", "b.PNG", "extra.png"],
        )

    def test_expand_input_each(self):
        groups = self.module.expand_input_each([self.input_dir])
        self.assertEqual(
            [[p.name for p in group] for group in groups],
            [["a.png"], ["b.PNG"]],
        )


if __name__ == "__main__":
    unittest.main()
