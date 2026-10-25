
import unittest
from unittest.mock import patch, MagicMock

from app.rag import RAG


class TestRAG(unittest.TestCase):

    @patch("app.rag.run_agent")
    def test_returns_unknown_when_no_documents(self, mock_agent):

        # 模拟 Agent 没有检索到任何文档
        mock_agent.return_value = {
            "success": False,
            "results": []
        }

        # 创建 RAG 对象，但不加载真实模型
        rag = RAG.__new__(RAG)
        rag.retriever = object()
        rag.llm = object()

        # 调用真正的 RAG.ask()
        answer, source = rag.ask(
            "What is the answer?",
            top_k=3
        )

        # 检查结果
        self.assertEqual(
            answer,
            "I don't know. No relevant information was found "
            "in the knowledge base."
        )

        self.assertIsNone(source)

    @patch("app.rag.run_agent")
    def test_fallback_when_reranker_returns_invalid_index(self, mock_agent):

        # 模拟 Agent 返回两个候选
        results = [
            {
                "text": "The database is Health Facts.",
                "metadata": {
                    "page": 2,
                    "chunk": 2,
                    "source": "study.pdf"
                },
                "score": 0.9
            },
            {
                "text": "Other background information.",
                "metadata": {
                    "page": 3,
                    "chunk": 1,
                    "source": "study.pdf"
                },
                "score": 0.7
            }
        ]

        mock_agent.return_value = {
            "success": True,
            "results": results
        }

        # 创建 RAG，跳过真实模型初始化
        rag = RAG.__new__(RAG)

        rag.retriever = MagicMock()
        rag.llm = MagicMock()

        # 第一次是 Reranker 输出，第二次是最终答案
        rag.llm.generate.side_effect = [
            "99",
            "The database is Health Facts."
        ]

        # 模拟构建生成 Prompt
        rag.retriever.build_prompt.return_value = "Answer the question."

        answer, source = rag.ask(
            "What database was used?",
            top_k=2
        )

        # 验证非法编号触发回退，选择第一个候选
        self.assertEqual(source["metadata"]["chunk"], 2)
        self.assertEqual(source["metadata"]["page"], 2)

        # 验证最终仍然返回答案
        self.assertEqual(answer, "The database is Health Facts.")

        # 验证 LLM 总共调用两次
        self.assertEqual(rag.llm.generate.call_count, 2)


if __name__ == "__main__":
    unittest.main()
