from ollama import chat
from app.config import LLM_MODEL
class LLM:

    def generate(self, prompt):
        response = chat(
            model = LLM_MODEL,
            messages = [
                {
                    "role" : "user",
                    "content" : prompt
                }
            ],
            options={
                "temperature": 0
            }
        )
        # print(response)
        return response["message"]["content"]

if __name__ == "__main__":

    llm = LLM()

    prompt = "Context: HbA1c is related to readmission."

    answer = llm.generate(prompt)

    print(answer)