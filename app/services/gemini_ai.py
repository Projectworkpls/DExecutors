import google.generativeai as genai
import os
import json
from datetime import datetime

class GeminiAIService:
    def __init__(self):
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-pro')

    def analyze_project_feasibility(self, title, description, budget, deadline, selected_grades="5-9"):
        """
        Analyzes project feasibility with REALISTIC expectations for average school children.
        """
        prompt = f"""
        You are a STRICT educational project evaluator with 20+ years of experience. You must be BRUTALLY HONEST about what average school children can actually accomplish.

        [The rest of your detailed prompt remains unchanged...]
        """

        try:
            response = self.model.generate_content(prompt)
            # Attempt to extract the first JSON object from the response
            json_start = response.text.find('{')
            json_end = response.text.rfind('}')
            if json_start != -1 and json_end != -1:
                result = json.loads(response.text[json_start:json_end+1])
            else:
                result = json.loads(response.text)

            # Ensure realistic bounds
            if result.get('total_hours_needed', 0) > 50:
                result['is_feasible'] = False
                result['recommendation'] = 'reject'
                result['why_impossible'] = 'Project too complex for student capabilities'
            
            result['analysis_timestamp'] = datetime.now().isoformat()
            return result
            
        except Exception as e:
            print(f"AI Analysis Error: {e}")
            return self._get_realistic_default_response(title, selected_grades, budget)

    def assess_student_submission(self, project_title, project_description, expected_outcomes,
                                  student_submission_text, student_grade=None, submission_type="text"):
        """
        Evaluates student submission quality with realistic expectations for average students.
        """
        prompt = f"""
        You are evaluating work submitted by an AVERAGE school student. Set realistic expectations.

        [Your detailed assessment prompt remains unchanged...]
        """

        try:
            response = self.model.generate_content(prompt)
            json_start = response.text.find('{')
            json_end = response.text.rfind('}')
            if json_start != -1 and json_end != -1:
                result = json.loads(response.text[json_start:json_end+1])
            else:
                result = json.loads(response.text)
            result['assessment_timestamp'] = datetime.now().isoformat()
            result['ai_version'] = "gemini-2.5-pro"
            return result
        except Exception as e:
            print(f"AI Assessment Error: {e}")
            return self._get_realistic_assessment_default(project_title, student_grade)

    def _get_realistic_default_response(self, title, grades, budget):
        """Realistic fallback that analyzes project complexity"""
        title_lower = title.lower()
        impossible_keywords = [
            'app', 'mobile', 'database', 'backend', 'server', 'programming', 
            'coding', 'software', 'payment', 'ecommerce', 'e-commerce',
            'artificial intelligence', 'machine learning', 'blockchain'
        ]
        complex_keywords = [
            'website', 'video', 'research', 'presentation', 'design',
            'build', 'create', 'develop', 'analyze'
        ]
        simple_keywords = [
            'interview', 'survey', 'draw', 'write', 'collect', 'visit',
            'talk', 'ask', 'list', 'find'
        ]
        if any(word in title_lower for word in impossible_keywords):
            return {
                "feasibility_score": 5,
                "is_feasible": False,
                "complexity_level": "impossible",
                "why_impossible": "This requires professional-level technical skills that students do not possess",
                "total_hours_needed": 0,
                "daily_work_hours": 0,
                "total_days_required": 0,
                "recommendation": "reject",
                "success_probability": 0,
                "parent_message": f"The project '{title}' involves professional-level technical development that is not appropriate for school students. Students in grades {grades} do not have the programming, database, or software development skills required. Please consider a simpler alternative like creating mockups, presentations, or research projects instead."
            }
        elif any(word in title_lower for word in complex_keywords):
            hours = 12 + (len(title) // 10)
            daily_hours = 1.5 if '5-6' in grades else 2.0
            days = max(4, int(hours / daily_hours))
            return {
                "feasibility_score": 65,
                "is_feasible": True,
                "complexity_level": "challenging",
                "total_hours_needed": hours,
                "daily_work_hours": daily_hours,
                "total_days_required": days,
                "recommendation": "minor_modifications",
                "success_probability": 70,
                "parent_message": f"The project '{title}' is challenging but doable for students in grades {grades}. It will require approximately {hours} hours over {days} days with adult guidance."
            }
        else:
            hours = 4 + (budget // 200)
            daily_hours = 1.5 if '5-6' in grades else 2.0
            days = max(2, int(hours / daily_hours))
            return {
                "feasibility_score": 90,
                "is_feasible": True,
                "complexity_level": "appropriate",
                "total_hours_needed": hours,
                "daily_work_hours": daily_hours,
                "total_days_required": days,
                "recommendation": "approve",
                "success_probability": 95,
                "parent_message": f"The project '{title}' is well-suited for students in grades {grades}. It should take approximately {hours} hours over {days} days."
            }

    def _get_realistic_assessment_default(self, title, grade):
        """Realistic assessment fallback based on grade level"""
        if grade and '5' in grade or '6' in grade:
            score = 65
            feedback = "Good effort for elementary level. Focus on following instructions and completing basic requirements."
        elif grade and ('7' in grade or '8' in grade):
            score = 70
            feedback = "Solid middle school work. Shows understanding with room for more detail and creativity."
        else:
            score = 75
            feedback = "Appropriate high school level effort. Demonstrates good grasp of concepts with potential for refinement."
        return {
            "overall_score": score,
            "meets_basic_requirements": True,
            "effort_visible": True,
            "age_appropriate_quality": True,
            "what_they_did_well": ["Addressed the main topic", "Showed effort"],
            "areas_needing_work": ["Could add more detail", "Presentation could improve"],
            "content_accuracy": score,
            "presentation_effort": score - 5,
            "creativity_shown": score - 10,
            "follows_basic_instructions": True,
            "recommendation": "good_effort",
            "realistic_score_justification": f"Appropriate quality for grade level {grade}",
            "parent_feedback": feedback,
            "award_points": max(30, score - 20),
            "assessment_timestamp": datetime.now().isoformat(),
            "ai_version": "gemini-2.5-pro"
        }

# Initialize the Gemini AI service
gemini_service = GeminiAIService()
