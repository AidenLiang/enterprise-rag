
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from fastapi.testclient import TestClient
from ollama import RequestError, ResponseError

from app.api.main import app


class TestRAGAPI(unittest.TestCase):

    def setUp(self):
        # Create a Mock RAG instead of loading the real model
        self.stack = ExitStack()

        self.mock_rag_class = self.stack.enter_context(
            patch("app.api.main.RAG")
        )

        self.mock_rag = self.mock_rag_class.return_value

        # Start TestClient and trigger FastAPI lifespan
        self.client = self.stack.enter_context(
            TestClient(app)
        )

    def tearDown(self):
        self.stack.close()

    def test_health_check(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok"}
        )

    def test_ask_returns_answer_and_sources(self):

        self.mock_rag.ask.return_value = (
            "The database was Health Facts.",
            {
                "metadata": {
                    "source": "description.pdf",
                    "page": 2,
                    "chunk": 2
                },
                "score": 0.90,
                "context_results": [
                    {
                        "metadata": {
                            "source": "description.pdf",
                            "page": 2,
                            "chunk": 2
                        },
                        "score": 0.90
                    },
                    {
                        "metadata": {
                            "source": "description.pdf",
                            "page": 2,
                            "chunk": 3
                        },
                        "score": 0.80
                    }
                ]
            }
        )

        response = self.client.post(
            "/ask",
            json={
                "query": "What database was used?",
                "top_k": 3
            }
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["answer"],
            "The database was Health Facts."
        )

        self.assertEqual(len(data["sources"]), 2)

        self.assertTrue(data["sources"][0]["selected"])
        self.assertFalse(data["sources"][1]["selected"])

        self.mock_rag.ask.assert_called_once_with(
            "What database was used?",
            top_k=3
        )

    def test_ask_rejects_invalid_input(self):

        response = self.client.post(
            "/ask",
            json={
                "query": "What database was used?",
                "top_k": 0
            }
        )

        self.assertEqual(response.status_code, 422)

        self.mock_rag.ask.assert_not_called()

    def test_ask_returns_503_when_request_fails(self):

        self.mock_rag.ask.side_effect = RequestError(
            "Ollama connection failed"
        )

        response = self.client.post(
            "/ask",
            json={
                "query": "What database was used?",
                "top_k": 3
            }
        )

        self.assertEqual(response.status_code, 503)

        self.assertEqual(
            response.json()["detail"],
            "LLM service is unavailable. Please try again later."
        )

    def test_ask_returns_502_when_response_fails(self):

        self.mock_rag.ask.side_effect = ResponseError(
            "Ollama returned an error",
            status_code=502
        )

        response = self.client.post(
            "/ask",
            json={
                "query": "What database was used?",
                "top_k": 3
            }
        )

        self.assertEqual(response.status_code, 502)

        self.assertEqual(
            response.json()["detail"],
            "LLM service returned an error. Please try again later."
        )


if __name__ == "__main__":
    unittest.main()
