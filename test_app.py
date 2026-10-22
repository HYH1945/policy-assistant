import unittest

from app import build_index, extract_evidence, search


class RetrievalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_index()

    def test_remote_work_exception(self):
        results = search("수습 직원도 재택근무할 수 있나요?", top_k=1)
        self.assertEqual(results[0]["doc_id"], "HR-REMOTE-2026")
        self.assertIn("수습 기간", results[0]["content"])
        self.assertIn("인사팀의 공동 승인", extract_evidence("수습 직원 재택근무", results))

    def test_travel_metadata_filter(self):
        results = search("부산 숙박비 한도", top_k=2, category="출장")
        self.assertTrue(results)
        self.assertTrue(all(result["category"] == "출장" for result in results))
        self.assertIn("13만원", results[0]["content"])

    def test_superseded_document_is_hidden(self):
        results = search("재택근무 주 2회", top_k=10)
        self.assertNotIn("HR-REMOTE-2025", {result["doc_id"] for result in results})


if __name__ == "__main__":
    unittest.main()
