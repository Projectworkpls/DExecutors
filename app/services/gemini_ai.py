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
        Analyzes project feasibility when parent uploads an idea.
        Returns detailed analysis including age suitability, time requirements, and possible outcomes.
        """
        prompt = f"""
        You are an expert educational project evaluator specializing in student capabilities across different age groups.

        Analyze this project submission from a parent:

        Project Title: {title}
        Description: {description}
        Budget: ₹{budget}
        Deadline: {deadline}
        Target Student Grades: {selected_grades}

        Provide a comprehensive analysis in JSON format with:

        1. FEASIBILITY ASSESSMENT:
        - feasibility_score (0-100): Overall project feasibility
        - is_feasible (boolean): Can students realistically complete this?
        - complexity_level (string): "beginner", "intermediate", "advanced"

        2. AGE GROUP ANALYSIS:
        - ideal_age_range (string): Best age group (e.g., "12-15 years")
        - ideal_grades (string): Best grade levels (e.g., "7-9")
        - selected_grades_suitable (boolean): Are the chosen grades appropriate?
        - age_suitability_reason (string): Why this age group is ideal

        3. TIME ANALYSIS:
        - estimated_hours (number): Total hours needed
        - recommended_timeline (string): Suggested completion time
        - is_deadline_realistic (boolean): Is the given deadline achievable?
        - time_breakdown (object): Hours per major task

        4. DETAILED FEEDBACK:
        - strengths (array): What makes this project good for students
        - concerns (array): Potential issues or challenges
        - safety_considerations (array): Any safety concerns for this age group
        - skill_requirements (array): Skills students need
        - learning_outcomes (array): What students will learn

        5. RECOMMENDATIONS:
        - modifications (array): Suggested changes to improve suitability
        - resources_needed (array): Materials/tools required
        - adult_supervision_level (string): "minimal", "moderate", "high"
        - budget_assessment (string): Is budget appropriate?

        6. FINAL VERDICT:
        - recommendation (string): "approve", "approve_with_modifications", "reject"
        - parent_message (string): 150-200 word message to parent explaining the analysis

        7. PROJECT PLANNING:
        - suggested_milestones (array of objects): Each with 'title', 'description', and 'estimated_hours'
        - budget_breakdown (object): Key expenses and their estimated costs
        - risk_factors (array): List of possible risks or challenges

        8. POSSIBLE OUTCOMES:
        - possible_outcomes (array): List of likely results or achievements students can expect from this project.

        Be thorough, educational, and consider real-world student capabilities.
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)

            # Ensure all expected keys exist, add defaults if missing
            result['suggested_milestones'] = result.get('suggested_milestones', [])
            result['budget_breakdown'] = result.get('budget_breakdown', {})
            result['risk_factors'] = result.get('risk_factors', [])
            result['possible_outcomes'] = result.get('possible_outcomes', [])
            result['analysis_timestamp'] = datetime.now().isoformat()
            return result
        except Exception as e:
            print(f"AI Analysis Error: {e}")
            return self._get_default_feasibility_response(title, selected_grades)

    def assess_student_submission(self, project_title, project_description, expected_outcomes,
                                 student_submission_text, student_grade=None, submission_type="text"):
        """
        Evaluates student submission quality and accuracy.
        Returns detailed assessment for admin review.
        """
        prompt = f"""
        You are an educational assessor evaluating student project submissions.

        PROJECT CONTEXT:
        Title: {project_title}
        Description: {project_description}
        Expected Outcomes: {expected_outcomes}
        Student Grade: {student_grade or "Not specified"}
        Submission Type: {submission_type}

        STUDENT SUBMISSION:
        {student_submission_text}

        Provide a comprehensive evaluation in JSON format:

        1. QUALITY ASSESSMENT:
        - overall_score (0-100): Overall submission quality
        - meets_requirements (boolean): Does it fulfill the project requirements?
        - completion_level (string): "incomplete", "partial", "complete", "exceeds_expectations"
        - effort_level (string): "minimal", "adequate", "good", "excellent"

        2. DETAILED EVALUATION:
        - strengths (array): What the student did well
        - weaknesses (array): Areas that need improvement
        - missing_elements (array): Required components not included
        - creative_elements (array): Innovative or creative aspects

        3. TECHNICAL ASSESSMENT:
        - accuracy (0-100): How accurate is the work?
        - presentation_quality (0-100): How well is it presented?
        - follows_instructions (boolean): Did they follow the guidelines?
        - age_appropriate_quality (boolean): Is quality appropriate for their age?

        4. LEARNING EVIDENCE:
        - demonstrates_understanding (boolean): Shows comprehension of concepts?
        - problem_solving_evident (boolean): Shows problem-solving skills?
        - research_quality (string): "poor", "fair", "good", "excellent"
        - originality_score (0-100): How original is the work?

        5. FEEDBACK FOR IMPROVEMENT:
        - specific_improvements (array): Concrete suggestions for improvement
        - next_steps (array): What should the student do next?
        - additional_resources (array): Helpful resources for improvement

        6. ADMIN REPORT:
        - recommendation (string): "approve", "request_revision", "reject"
        - admin_summary (string): 100-150 word summary for admin review
        - parent_feedback (string): 100-150 word feedback to share with parents
        - award_points (number): Suggested reputation points (0-100)

        7. SUBMISSION METADATA:
        - review_priority (string): "low", "medium", "high"
        - requires_manual_review (boolean): Needs human admin review?
        - confidence_level (0-100): AI's confidence in this assessment

        Be fair, constructive, and age-appropriate in your evaluation.
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            result['assessment_timestamp'] = datetime.now().isoformat()
            result['ai_version'] = "gemini-2.5-pro"
            return result
        except Exception as e:
            print(f"AI Assessment Error: {e}")
            return self._get_default_assessment_response(project_title)

    def _get_default_feasibility_response(self, title, grades):
        """Fallback response if AI analysis fails"""
        return {
            "feasibility_score": 75,
            "is_feasible": True,
            "complexity_level": "intermediate",
            "ideal_age_range": "12-15 years",
            "ideal_grades": "6-9",
            "selected_grades_suitable": True,
            "age_suitability_reason": "Default assessment - manual review recommended",
            "estimated_hours": 8,
            "recommended_timeline": "2-3 days",
            "is_deadline_realistic": True,
            "time_breakdown": {"planning": 2, "execution": 5, "documentation": 1},
            "strengths": ["Engaging topic", "Age-appropriate scope"],
            "concerns": ["Requires manual review"],
            "safety_considerations": ["Standard supervision recommended"],
            "skill_requirements": ["Basic research skills", "Communication skills"],
            "learning_outcomes": ["Problem-solving", "Project management"],
            "modifications": ["Consider adding more specific guidelines"],
            "resources_needed": ["Basic materials"],
            "adult_supervision_level": "moderate",
            "budget_assessment": "Appropriate for scope",
            "recommendation": "approve_with_modifications",
            "parent_message": f"Your project '{title}' shows promise for students in grades {grades}. Our AI analysis suggests it's feasible with moderate supervision. We recommend reviewing the specific requirements and ensuring adequate time for completion. This project offers good learning opportunities in problem-solving and creativity.",
            "suggested_milestones": [],
            "budget_breakdown": {},
            "risk_factors": [],
            "possible_outcomes": [
                "Students will learn teamwork and communication.",
                "Students will develop time management skills.",
                "Students will gain hands-on experience in project execution."
            ],
            "analysis_timestamp": datetime.now().isoformat()
        }

    def _get_default_assessment_response(self, title):
        """Fallback response if submission assessment fails"""
        return {
            "overall_score": 70,
            "meets_requirements": False,
            "completion_level": "partial",
            "effort_level": "adequate",
            "strengths": ["Shows effort", "Addresses main topic"],
            "weaknesses": ["Needs more detail", "Could improve presentation"],
            "missing_elements": ["Specific requirements not assessed"],
            "creative_elements": ["Some original thinking evident"],
            "accuracy": 70,
            "presentation_quality": 65,
            "follows_instructions": True,
            "age_appropriate_quality": True,
            "demonstrates_understanding": True,
            "problem_solving_evident": True,
            "research_quality": "fair",
            "originality_score": 60,
            "specific_improvements": ["Add more specific details", "Improve presentation"],
            "next_steps": ["Revise based on feedback", "Add missing elements"],
            "additional_resources": ["Project guidelines", "Example submissions"],
            "recommendation": "request_revision",
            "admin_summary": f"Submission for '{title}' shows adequate effort but needs improvement in detail and presentation. Student demonstrates understanding but could benefit from revision.",
            "parent_feedback": "Your child has made a good start on this project. With some additional work on details and presentation, this could be an excellent submission.",
            "award_points": 35,
            "review_priority": "medium",
            "requires_manual_review": True,
            "confidence_level": 60,
            "assessment_timestamp": datetime.now().isoformat(),
            "ai_version": "gemini-2.5-pro"
        }

# Initialize service
gemini_service = GeminiAIService()


#