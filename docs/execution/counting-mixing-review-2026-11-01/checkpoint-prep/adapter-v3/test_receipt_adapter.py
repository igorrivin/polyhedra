import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checkpoint_lib import CheckpointError, load_json
from candidate_receipt_adapter import whitespace_record

class WhitespaceAdapterTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).resolve().parents[2]/"source-checkpoint"
        self.row=load_json(base/"stage.json")["whitespace_checks"][0]
        self.exception=load_json(base/"root-whitespace-exception.json")
        self.command=["git","diff","--cached","--check"]
    def validate(self,row=None,exception=None):
        whitespace_record(self.row if row is None else row,self.exception if exception is None else exception,self.command)
    def test_actual_five_path_exception_passes(self): self.validate()
    def test_extra_disabled_rule_rejected(self):
        row=copy.deepcopy(self.row);row["adjusted_core_whitespace"]="-blank-at-eof,-trailing-space"
        with self.assertRaises(CheckpointError): self.validate(row)
    def test_added_diagnostic_rejected(self):
        row=copy.deepcopy(self.row);row["original_diagnostics"].append("other.tex:1: trailing whitespace.")
        with self.assertRaises(CheckpointError): self.validate(row)
    def test_default_failure_cannot_be_relabelled_success(self):
        record=copy.deepcopy(self.exception);record["original_command_returncode"]=0
        with self.assertRaises(CheckpointError): self.validate(exception=record)
    def test_effective_failure_rejected(self):
        row=copy.deepcopy(self.row);row["adjusted_check_returncode"]=2
        with self.assertRaises(CheckpointError): self.validate(row)
    def test_effective_diagnostic_rejected(self):
        row=copy.deepcopy(self.row);row["adjusted_check_output"]="warning"
        with self.assertRaises(CheckpointError): self.validate(row)
    def test_scope_authority_changes_rejected(self):
        record=copy.deepcopy(self.exception);record["source_edits_authorized"]=True
        with self.assertRaises(CheckpointError): self.validate(exception=record)
    def test_preexisting_configuration_not_silently_ignored(self):
        row=copy.deepcopy(self.row);row["prior_core_whitespace"]="-trailing-space"
        with self.assertRaises(CheckpointError): self.validate(row)
if __name__=="__main__": unittest.main()
