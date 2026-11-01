import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checkpoint_lib import CheckpointError, load_json
from source_approval_adapter import approved_source_map

class ApprovalShapeTests(unittest.TestCase):
    def setUp(self):
        self.record = load_json(Path(__file__).resolve().parents[2] / "integration-review/revision-v2/approved-source-manifest.json")
        self.pin = {"source_sha256_pointer": "/approved_sources", "source_sha256_shape": "path-record-list"}
    def test_actual_final_33_path_approval(self):
        result = approved_source_map(self.record, self.pin)
        self.assertEqual(len(result), 33)
        self.assertEqual(result, {r["path"]:r["sha256"] for r in self.record["approved_sources"]})
    def test_legacy_mapping_retains_exact_values(self):
        value = {"source.py": "a"*64}
        self.assertEqual(approved_source_map({"files": value}, {"source_sha256_pointer":"/files"}), value)
    def test_duplicate_path_is_rejected(self):
        record=copy.deepcopy(self.record); record["approved_sources"].append(record["approved_sources"][0])
        with self.assertRaises(CheckpointError): approved_source_map(record,self.pin)
    def test_wrong_explicit_shape_is_rejected(self):
        with self.assertRaises(CheckpointError): approved_source_map(self.record,{"source_sha256_pointer":"/approved_sources"})
    def test_bad_digest_is_rejected(self):
        record=copy.deepcopy(self.record);record["approved_sources"][0]["sha256"]="bad"
        with self.assertRaises(CheckpointError): approved_source_map(record,self.pin)
    def test_empty_or_unknown_shape_is_rejected(self):
        with self.assertRaises(CheckpointError): approved_source_map({"files":{}},{"source_sha256_pointer":"/files"})
        with self.assertRaises(RuntimeError): approved_source_map(self.record,self.pin|{"source_sha256_shape":"guess"})
if __name__ == "__main__": unittest.main()
