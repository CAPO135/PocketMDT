from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


class GastroenterologistAgent:
    description = (
        "Analyzes gut health, liver enzyme patterns, microbiome status, GI inflammation, malabsorption, and digestive symptoms. "
        "Focuses on liver markers (AST, ALT, ALP, GGT, bilirubin), stool results, GI-related symptoms, and medication impact on the digestive system."
    )

    def __init__(self, model_name="gpt-4", temperature=0):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.prompt_template = PromptTemplate.from_template("""
You are a clinical gastroenterologist AI. Analyze the following data to identify signs of GI dysfunction, liver enzyme abnormalities, or digestive issues.

User Question:
{user_input}

IMPORTANT: The following information comes from uploaded medical documents and lab reports. Use this as your primary source for analysis.

Document Context (from uploaded medical files):
{document_context}

Structure your response using:
1. Summary of Findings
2. Clinical Interpretation
3. Recommendations
4. Follow-Up or Gaps in Data

Note: If the uploaded documents contain relevant lab results, test data, or medical information, reference them specifically in your analysis. Base your recommendations on the actual data provided in the documents.
""")

    def run(self, context):
        user_input = context.get("user_input", "No user question provided.")
        document_context = context.get("document_context", "No document context provided.")
        prompt = self.prompt_template.format(user_input=user_input, document_context=document_context)
        response = self.llm.predict(prompt)
        return response



