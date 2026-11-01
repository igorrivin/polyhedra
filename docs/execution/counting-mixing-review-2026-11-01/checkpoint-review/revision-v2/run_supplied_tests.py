"""Run exact copied author tests, relocating only their read-only fixture root."""
import importlib
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "subject"))
test_checkpoint = importlib.import_module("test_checkpoint")
test_checkpoint_revision = importlib.import_module("test_checkpoint_revision")

OUTER = HERE.parent.parent
test_checkpoint.OUTER = OUTER
test_checkpoint_revision.OUTER = OUTER
suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromModule(test_checkpoint),
    unittest.defaultTestLoader.loadTestsFromModule(test_checkpoint_revision),
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
