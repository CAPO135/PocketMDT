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

Structure your response using the following format:

## SPECIFIC FINDINGS FROM DOCUMENTS
- Extract and list ALL relevant lab values, test results, and clinical findings from the uploaded documents
- Include exact numbers, dates, and measurements when available
- Quote specific text from the documents that supports your analysis

## CLINICAL INTERPRETATION
- Interpret the specific findings you extracted above
- Explain what each lab value or finding means in clinical terms
- Identify any abnormal values and their significance

## ENDOCRINE SYSTEM ASSESSMENT
- Thyroid function (TSH, T4, T3, antibodies)
- Adrenal function (cortisol, ACTH)
- Pancreatic function (glucose, insulin, A1C)
- Reproductive hormones (testosterone, estrogen, progesterone)
- Pituitary function (if applicable)

## TRENDS AND PATTERNS
- Identify any trends over time if multiple tests are available
- Note any correlations between different hormone systems
- Highlight any concerning patterns or improvements

## RECOMMENDATIONS
- Specific recommendations based on the actual data from the documents
- Suggested follow-up tests or monitoring
- Lifestyle or treatment considerations

## DATA GAPS
- Note any missing information that would be helpful for a complete assessment
- Suggest additional tests that could provide more insight

IMPORTANT: Always reference specific data from the uploaded documents. If no relevant endocrine data is found in the documents, clearly state this and explain what information would be needed for a proper endocrine assessment.
""")

    def run(self, context):
        user_input = context.get("user_input", "No user question provided.")
        document_context = context.get("document_context", "No document context provided.")
        prompt = self.prompt_template.format(user_input=user_input, document_context=document_context)
        response = self.llm.invoke(prompt)
        return response.content



