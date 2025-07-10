from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


class EndocrinologistAgent:
    description = (
      
    "Evaluates hormonal and endocrine system health including thyroid, adrenal, pancreatic, reproductive, and pituitary axes. "
    "Analyzes labs such as TSH, Free T4, Free T3, cortisol, insulin, A1C, testosterone, and estrogen. "
    "Assesses conditions like hypothyroidism, insulin resistance, adrenal fatigue, and hormone imbalance. "
    "Links lab findings to symptoms such as fatigue, weight changes, sleep disruption, menstrual irregularity, and metabolic dysfunction."
    )
    

    def __init__(self, model_name="gpt-4", temperature=0):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.prompt_template = PromptTemplate.from_template("""
You are a clinical endocrinologist AI. Analyze the following data to assess thyroid, adrenal, pancreatic, and reproductive hormone function. Identify signs of hormonal imbalance, metabolic dysfunction, or endocrine-related trends.

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



