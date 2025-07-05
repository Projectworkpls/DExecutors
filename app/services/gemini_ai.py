import google.generativeai as genai
import os
import json

class GeminiAIService:
    def __init__(self):
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-pro')  # Updated model name

    def analyze_project_feasibility(self, title, description, budget, deadline):
        prompt = f"""
        Analyze this project for feasibility:
        Title: {title}
        Description: {description}
        Budget: ₹{budget}
        Deadline: {deadline}

        Provide a JSON response with:
        - feasibility_score (0-100)
        - suggested_milestones (array of milestone objects)
        - budget_breakdown (object)
        - risk_factors (array)
        - recommendations (array)
        """

        response = self.model.generate_content(prompt)
        try:
            return json.loads(response.text)
        except:
            return {
                "feasibility_score": 75,
                "suggested_milestones": [],
                "budget_breakdown": {},
                "risk_factors": [],
                "recommendations": []
            }

gemini_service = GeminiAIService()
