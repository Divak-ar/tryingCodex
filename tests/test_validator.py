import unittest

from rag_abap_validator import ABAPRAGValidator


class ValidatorTests(unittest.TestCase):
    def test_autofix_brings_design_to_pass(self):
        design = {
            "data_sources": {"supported_doc_types": ["ABAP Functional Spec"]},
            "chunking": {"strategy": "fixed", "max_tokens": 200, "overlap_tokens": 10},
            "retrieval": {"mode": "vector", "top_k": 3, "metadata_fields": ["doc_id"]},
            "generation": {"model": "x"},
            "evaluation": {"metrics": {"groundedness": 0.5}, "golden_set_size": 5},
        }
        reports = ABAPRAGValidator({}, design).run_improvement_loop(max_iterations=3, apply_fixes=True)
        self.assertTrue(reports[-1].passed)

    def test_evaluation_only_stays_failed_when_gaps_exist(self):
        design = {
            "data_sources": {"supported_doc_types": ["ABAP Functional Spec"]},
            "chunking": {"strategy": "fixed", "max_tokens": 200, "overlap_tokens": 10},
        }
        reports = ABAPRAGValidator({}, design).run_improvement_loop(max_iterations=1, apply_fixes=False)
        self.assertFalse(reports[-1].passed)


if __name__ == "__main__":
    unittest.main()
