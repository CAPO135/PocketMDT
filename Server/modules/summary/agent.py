from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

class SummaryAgent:
    def __init__(self, model_name="gpt-4", temperature=0.3):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.prompt_template = PromptTemplate.from_template("""
You are a medical summarization assistant. Your task is to compile insights from multiple domain-specific clinical specialists into a single coherent, patient-friendly report.

Use a professional but accessible tone. Organize the output by medical domain.

Inputs:
{agent_outputs}

Output Format:
1. Overview
2. Findings by Specialty (Nephrology, Cardiology, Gastroenterology, Endocrinology, etc.)
3. Recommended Next Steps
""")

    def summarize(self, agent_outputs, context):
        input_data = ""
        for agent_name, output in agent_outputs.items():
            input_data += f"\n[{agent_name}]\n{output}\n"

        prompt = self.prompt_template.format(agent_outputs=input_data.strip())
        response = self.llm.invoke(prompt)
        return response.content
