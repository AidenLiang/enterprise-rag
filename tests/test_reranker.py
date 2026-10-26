
import unittest

from app.reranking.reranker import parse_rerank_index


class TestParseRerankIndex(unittest.TestCase):

    def test_parses_plain_number(self):
        result = parse_rerank_index("2", 5)
        self.assertEqual(result, 1)

    def test_parses_candidate_number(self):
        result = parse_rerank_index("Candidate 2.", 5)
        self.assertEqual(result, 1)

    def test_parses_candidate_with_colon(self):
        result = parse_rerank_index("Candidate: 3", 5)
        self.assertEqual(result, 2)

    def test_rejects_out_of_range_number(self):
        result = parse_rerank_index("Candidate 6.", 5)
        self.assertIsNone(result)

    def test_rejects_invalid_format(self):
        invalid_answers = [
            "",
            "I think Candidate 2 is correct.",
            "two",
            "Candidate",
        ]

        for answer in invalid_answers:
            with self.subTest(answer=answer):
                result = parse_rerank_index(answer, 5)
                self.assertIsNone(result)

    def test_rejects_non_string_input(self):
        result = parse_rerank_index(None, 5)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
