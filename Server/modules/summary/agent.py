from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

class SummaryAgent:
    def __init__(self, model_name="gpt-4", temperature=0.3):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.prompt_template = PromptTemplate.from_template("""
You are a medical summarization assistant. Your task is to compile insights from multiple domain-specific clinical specialists into a single coherent, patient-friendly report that provides a comprehensive health overview.

Use a professional but accessible tone. Organize the output by medical domain and identify cross-specialty correlations.

Specialist Inputs:
{agent_outputs}

User's Original Question:
{user_question}

Output Format:

## EXECUTIVE SUMMARY
Provide a concise overview of the most important findings and recommendations across all specialties.

## FINDINGS BY SPECIALTY
### Cardiology (Heart & Circulation)
- Key cardiovascular findings and risk factors
- Blood pressure, cholesterol, and heart function assessment

### Endocrinology (Hormones & Metabolism)
- Hormone levels and metabolic health
- Thyroid, diabetes, and adrenal function

### Gastroenterology (Digestive System)
- Liver function and digestive health
- GI symptoms and gut health assessment

### Nephrology (Kidney Function)
- Kidney function and fluid balance
- Electrolyte levels and renal health

### Neurology (Brain & Nervous System)
- Cognitive function and neurological health
- Any neurological symptoms or concerns

### Ophthalmology (Eye Health)
- Vision and eye health assessment
- Retinal health and systemic disease correlations

### General Medicine
- Overall health patterns and general findings
- Preventive care recommendations

## CROSS-SPECIALTY CORRELATIONS
Identify connections between different organ systems and how conditions in one specialty may affect others (e.g., diabetes affecting eyes, kidneys, and heart).

## PRIORITY RECOMMENDATIONS
1. **Immediate Actions** - Any urgent concerns requiring prompt attention
2. **Short-term Goals** - Actions to take within the next 1-3 months
3. **Long-term Management** - Ongoing monitoring and lifestyle considerations

## FOLLOW-UP PLAN
- Suggested timeline for follow-up appointments
- Recommended additional tests or screenings
- Monitoring parameters and frequency

## QUESTIONS FOR YOUR HEALTHCARE PROVIDER
Provide 3-5 specific questions the patient should ask their healthcare provider based on the findings.

Note: This summary is based on analysis of your uploaded medical documents. Always consult with your healthcare provider for personalized medical advice and treatment decisions.
""")

    def summarize(self, agent_outputs, context):
        user_question = context.get("user_input", "General health assessment")
        
        input_data = ""
        for agent_name, output in agent_outputs.items():
            # Clean up agent name for display
            clean_name = agent_name.replace("Agent", "").replace("ist", "ology" if agent_name.endswith("istAgent") else "")
            input_data += f"\n[{clean_name}]\n{output}\n"

        prompt = self.prompt_template.format(
            agent_outputs=input_data.strip(),
            user_question=user_question
        )
        response = self.llm.invoke(prompt)
        return response.content
