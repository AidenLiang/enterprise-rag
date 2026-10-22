
import unittest
from unittest.mock import Mock
from app.agent.tools import (
    retrieve_documents,
    rewrite_query,
    assess_evidence,
)
from app.config import TOP_K, RETRIEVAL_THRESHOLD


class TestRetrieveDocuments(unittest.TestCase):

    def setUp(self):
        self.fake_retriever = Mock()
        self.query = "What database was used in the study?"
        
    def test_returns_retrieval_results(self):

        # 1. Prepare a fake retriever
        expected_results = [
            {
                "text": "Health Facts database",
                "metadata": {"page": 2, "chunk": 3},
                "score": 0.48
            }
        ]

        # fake_retriever = Mock()
        self.fake_retriever.retrieve.return_value = expected_results

        # 2. Call the tool
        # query = "What database was used in the study?"

        actual_results = retrieve_documents(
            self.fake_retriever,
            self.query,
            top_k=3,
            threshold=-1
        )

        # 3. Check the returned results
        self.assertEqual(actual_results, expected_results)

        # 4. Check whether retrieve() was called correctly
        self.fake_retriever.retrieve.assert_called_once_with(
            self.query,
            top_k=3,
            threshold=-1
        )

    def test_uses_default_parameters(self):
        self.fake_retriever.retrieve.return_value = []
        # query = "test question"
        results = retrieve_documents(self.fake_retriever, self.query)
        self.assertEqual(results, [])
            
        self.fake_retriever.retrieve.assert_called_once_with(
        self.query,
        top_k=TOP_K,
        threshold=RETRIEVAL_THRESHOLD
        )

    
        
class TestRewriteQuery(unittest.TestCase):

    def setUp(self):
        self.fake_llm = Mock()
        self.query = "What database was used in the study?"
        self.feedback = "The retrieved evidence was insufficient."

    def test_rewrite_query_returns_clean_text(self):
        # 1. Create a fake LLM

        self.fake_llm.generate.return_value = "  Rewritten query  \n"

        # 2. Call rewrite_query()
        result = rewrite_query(self.fake_llm, self.query, self.feedback)

        # 3. Check the returned text
        self.assertEqual(result, "Rewritten query")

        # 4. Check that the LLM was called once
        self.fake_llm.generate.assert_called_once()

        # 5. Check the prompt passed to the LLM
        prompt = self.fake_llm.generate.call_args.args[0]

        self.assertIn(self.query, prompt)
        self.assertIn(self.feedback, prompt)

class TestAssessEvidence(unittest.TestCase):
    
    def setUp(self):
        self.fake_llm = Mock()
        self.query = "What database was used in the study?"
        self.results = [
            {"text": "The study discusses external data limitations."}
        ]

    def test_assess_evidence_accepts_valid_false(self):
    
        self.fake_llm.generate.return_value = (
            '{"sufficient": false, '
            '"feedback": "The database name is missing."}'
        )

        

        result = assess_evidence(self.fake_llm, self.query, self.results)

        expected = {
            "sufficient": False,
            "feedback": "The database name is missing."
        }

        self.assertEqual(result, expected)
        self.fake_llm.generate.assert_called_once()

    def test_assess_evidence_handles_invalid_json(self):
        

        # 1. Simulate an invalid JSON response
        self.fake_llm.generate.return_value = "This is not valid JSON"


        # 3. Call the function
        result = assess_evidence(self.fake_llm, self.query, self.results)

        # 4. Check the safe fallback result
        expected = {
            "sufficient": False,
            "feedback": "Error decoding response!"
        }

        self.assertEqual(result, expected)

        # 5. Check that the LLM was called once
        self.fake_llm.generate.assert_called_once()



    def test_assess_evidence_handles_empty_results(self):
        
        self.results = []

        # 2. Call the function
        result = assess_evidence(self.fake_llm, self.query, self.results)

        # 3. Check the returned result
        expected = {
            "sufficient": False,
            "feedback": "No documents were retrieved."
        }

        self.assertEqual(result, expected)

        # 4. Check that the LLM was NOT called
        self.fake_llm.generate.assert_not_called()


    def test_assess_evidence_rejects_invalid_field_type(self):
        self.fake_llm.generate.return_value = (
            '{"sufficient": "false", '
            '"feedback": "The database name is missing."}'
        )


        result = assess_evidence(self.fake_llm, self.query, self.results)

        expected = {
            "sufficient": False,
            "feedback": "Error Type!"
        }

        self.assertEqual(result, expected)
        self.fake_llm.generate.assert_called_once()
        
    def test_assess_evidence_rejects_invalid_feedback_type(self):
        self.fake_llm.generate.return_value = (
            '{"sufficient": true, "feedback": 123}'
        )

        result = assess_evidence(
            self.fake_llm,
            self.query,
            self.results
        )

        expected = {
            "sufficient": False,
            "feedback": "Error Type!"
        }

        self.assertEqual(result, expected)
        self.fake_llm.generate.assert_called_once()




if __name__ == "__main__":
    unittest.main()
