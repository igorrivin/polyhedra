"""Run unchanged copied tests against frozen v3 modules, with read-only routing."""
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
OUTER = HERE.parent.parent
SUBJECT = HERE / "subject"
sys.path.insert(0, str(SUBJECT))
for name in ("checkpoint_lib", "source_approval_adapter", "candidate_receipt_adapter", "compare_replays", "run_clean_replay", "verify_checkpoint"):
    importlib.import_module(name)
suite = unittest.TestSuite()
for name in ("test_checkpoint", "test_checkpoint_revision", "test_approval_shape", "test_receipt_adapter"):
    is_adapter = name in ("test_approval_shape", "test_receipt_adapter")
    path = HERE / "adapter-tests" / (name + ".py") if is_adapter else HERE.parent / "revision-v2/subject" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if is_adapter:
        module.__file__ = str(OUTER / "checkpoint-prep/adapter-v3" / (name + ".py"))
    else:
        module.HERE = SUBJECT
        module.OUTER = OUTER
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
