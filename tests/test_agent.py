
import unittest
from unittest.mock import Mock, patch

from app.agent.agent import run_agent


class TestRunAgent(unittest.TestCase):

    def test_stops_when_evidence_is_sufficient(self):
        # 1. Prepare fake objects and expected data
        fake_retriever = Mock()
        fake_llm = Mock()

        query = "What database was used in the study?"

        fake_results = [
            {
                "text": "This study used the Health Facts database.",
                "metadata": {"page": 2, "chunk": 3},
                "score": 0.48
            }
        ]

        sufficient_assessment = {
            "sufficient": True,
            "feedback": "The database name is explicitly stated."
        }

        # 2. Replace the three tools with controlled mocks
        with (
            patch(
                "app.agent.agent.retrieve_documents",
                return_value=fake_results
            ) as mock_retrieve,
            patch(
                "app.agent.agent.assess_evidence",
                return_value=sufficient_assessment
            ) as mock_assess,
            patch(
                "app.agent.agent.rewrite_query"
            ) as mock_rewrite,
        ):

            # 3. Run the agent
            result = run_agent(
                query,
                fake_retriever,
                fake_llm
            )

            # 4. Check tool calls
            mock_retrieve.assert_called_once_with(
                fake_retriever,
                query
            )

            mock_assess.assert_called_once_with(
                fake_llm,
                query,
                fake_results
            )

            mock_rewrite.assert_not_called()

        # 5. Check the final result
        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["final_query"], query)
        self.assertEqual(result["results"], fake_results)


    def test_retries_when_evidence_is_insufficient(self):
        # 1. Prepare fake objects
        fake_retriever = Mock()
        fake_llm = Mock()

        query = "What database was used in the study?"
        rewritten_query = (
            "What clinical database was used to store patient records?"
        )

        first_results = [
            {
                "text": "The study discusses external data limitations.",
                "metadata": {"page": 2, "chunk": 2},
                "score": 0.49
            }
        ]

        second_results = [
            {
                "text": "This study used the Health Facts database.",
                "metadata": {"page": 2, "chunk": 3},
                "score": 0.62
            }
        ]

        insufficient_assessment = {
            "sufficient": False,
            "feedback": (
                "The retrieved documents do not clearly identify "
                "the database name."
            )
        }

        sufficient_assessment = {
            "sufficient": True,
            "feedback": "The database name is explicitly stated."
        }

        # 2. Mock the tools used by the agent
        with (
            patch(
                "app.agent.agent.retrieve_documents",
                side_effect=[first_results, second_results]
            ) as mock_retrieve,
            patch(
                "app.agent.agent.assess_evidence",
                side_effect=[
                    insufficient_assessment,
                    sufficient_assessment
                ]
            ) as mock_assess,
            patch(
                "app.agent.agent.rewrite_query",
                return_value=rewritten_query
            ) as mock_rewrite,
        ):

            # 3. Run the agent with one allowed retry
            result = run_agent(
                query,
                fake_retriever,
                fake_llm,
                max_retries=1
            )

            # 4. Check the tool call counts
            self.assertEqual(mock_retrieve.call_count, 2)
            self.assertEqual(mock_assess.call_count, 2)
            mock_rewrite.assert_called_once_with(
                fake_llm,
                query,
                insufficient_assessment["feedback"]
            )

            # 5. Check the final result
            self.assertTrue(result["success"])
            self.assertEqual(result["attempts"], 2)
            self.assertEqual(result["final_query"], rewritten_query)
            self.assertEqual(result["results"], second_results)


    def test_stops_when_retries_are_exhausted(self):
        fake_retriever = Mock()
        fake_llm = Mock()

        query = "What database was used in the study?"
        rewritten_query = (
            "What clinical database was used to store patient records?"
        )

        first_results = [
            {"text": "The study discusses external data limitations."}
        ]

        second_results = [
            {"text": "The retrieved evidence is still insufficient."}
        ]

        insufficient_assessment = {
            "sufficient": False,
            "feedback": "The database name is still unclear."
        }

        with (
            patch(
                "app.agent.agent.retrieve_documents",
                side_effect=[first_results, second_results]
            ) as mock_retrieve,
            patch(
                "app.agent.agent.assess_evidence",
                return_value=insufficient_assessment
            ) as mock_assess,
            patch(
                "app.agent.agent.rewrite_query",
                return_value=rewritten_query
            ) as mock_rewrite,
        ):
            result = run_agent(
                query,
                fake_retriever,
                fake_llm,
                max_retries=1
            )

            self.assertEqual(mock_retrieve.call_count, 2)
            self.assertEqual(mock_assess.call_count, 2)
            mock_rewrite.assert_called_once()

        self.assertFalse(result["success"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["final_query"], rewritten_query)
        self.assertEqual(result["results"], second_results)

if __name__ == "__main__":
    unittest.main()
