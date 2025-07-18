import google.generativeai as genai
from flask import current_app
import json
import base64
from PIL import Image
import io
import re

class GeminiService:
    def __init__(self):
        self.model = None
        self.chat_model = None
        self.vision_model = None
        self._api_key = None
        self._chat_sessions = {}  # Store chat sessions in memory with session IDs

    def init_app(self, app):
        try:
            self._api_key = app.config.get('GEMINI_API_KEY')

            print(f"Initializing Gemini with API key present: {bool(self._api_key)}")

            if not self._api_key:
                print("ERROR: Missing Gemini API key in environment")
                return

            genai.configure(api_key=self._api_key)

            # Configuration for free tier usage
            self.generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,  # Reduced for free tier
            }

            self.safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]

            # Use Gemini 2.0 Flash (free tier)
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            # For vision tasks, use the same model (2.0 Flash supports vision)
            self.vision_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            print("Gemini 2.0 Flash service initialized successfully")

        except Exception as e:
            print(f"Failed to initialize Gemini service: {e}")
            self.model = None
            self.vision_model = None

    def get_model(self):
        if self.model is None and self._api_key:
            print("Reinitializing Gemini 2.0 Flash model...")
            try:
                genai.configure(api_key=self._api_key)
                self.model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                print("Gemini 2.0 Flash model reinitialized successfully")
            except Exception as e:
                print(f"Failed to reinitialize Gemini: {e}")
        return self.model

    def start_project_evaluation_chat(self, project_title, project_description):
        """Start an interactive chat to evaluate project feasibility and parameters"""

        model = self.get_model()
        if model is None:
            return {
                "success": False,
                "error": "Gemini service not available"
            }

        initial_prompt = f"""
        You are an educational project advisor helping to evaluate a project idea submitted by a parent for school students.

        Project Title: {project_title}
        Project Description: {project_description}

        Your task is to:
        1. Ask clarifying questions to understand the project better
        2. Assess age-appropriateness and feasibility for average school students
        3. Determine realistic time requirements
        4. Establish clear evaluation parameters
        5. Recommend the BEST submission format for student work evaluation

        Start by asking 2-3 specific questions about:
        - The expected deliverables
        - Required skills or materials
        - Target age group specifics
        - Success criteria

        Also consider what format would best showcase the student's work:
        - VIDEO: For demonstrations, presentations, or process documentation
        - IMAGE: For visual arts, crafts, or static displays
        - URL: For websites, apps, or online content
        - PDF: For research reports, written analysis, or documentation
        - TEXT: For essays, stories, or simple written responses

        Keep your questions concise and focused. After gathering information, you'll provide a comprehensive evaluation report with a recommended submission format.
        """

        try:
            chat = model.start_chat(history=[])
            response = chat.send_message(initial_prompt)

            # Generate a unique session ID
            import uuid
            session_id = str(uuid.uuid4())

            # Store the chat session in memory
            self._chat_sessions[session_id] = chat

            return {
                "success": True,
                "chat_id": session_id,
                "response": response.text,
                "chat_session": session_id  # Return session ID instead of chat object
            }
        except Exception as e:
            print(f"Error starting project evaluation chat: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def continue_project_evaluation_chat(self, session_id, user_response):
        """Continue the project evaluation conversation"""

        try:
            # Get the chat session from memory
            if session_id not in self._chat_sessions:
                return {
                    "success": False,
                    "error": "Chat session not found"
                }

            chat_session = self._chat_sessions[session_id]
            response = chat_session.send_message(user_response)
            return {
                "success": True,
                "response": response.text
            }
        except Exception as e:
            print(f"Error continuing chat: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def finalize_project_evaluation(self, session_id):
        """Generate final project evaluation report using structured prompting"""

        try:
            # Get the chat session from memory
            if session_id not in self._chat_sessions:
                return {
                    "success": False,
                    "error": "Chat session not found"
                }

            chat_session = self._chat_sessions[session_id]

            finalization_prompt = """
            Based on our conversation, please provide a comprehensive evaluation report. 
            Structure your response with clear sections and specific details:

            AGE APPROPRIATENESS:
            - Recommended age range: [specify range]
            - Grade levels: [list applicable grades]
            - Complexity score (1-10): [score]
            - Reasoning: [explanation]

            FEASIBILITY:
            - Difficulty level: [beginner/intermediate/advanced]
            - Estimated time: [hours]
            - Required materials: [list items]
            - Required skills: [list skills]
            - Feasibility score (1-10): [score]

            EVALUATION PARAMETERS:
            - Creativity weight: [percentage]
            - Technical execution weight: [percentage]
            - Presentation quality weight: [percentage]
            - Adherence to brief weight: [percentage]
            - Specific criteria: [list criteria]

            RECOMMENDED CREDITS:
            - Minimum credits: [number]
            - Maximum credits: [number]
            - Bonus criteria: [list criteria]

            SUBMISSION FORMAT RECOMMENDATION:
            - Recommended format: [video/image/url/pdf/text]
            - Format reasoning: [why this format is best for evaluation]

            CHALLENGES AND SUCCESS:
            - Potential challenges: [list challenges]
            - Success indicators: [list indicators]

            Please ensure evaluation weights total 100% and assessments are realistic for school students. Give reason for all marks and scores.
            """

            response = chat_session.send_message(finalization_prompt)
            response_text = response.text

            # Parse the structured response instead of JSON
            evaluation_data = self._parse_structured_evaluation(response_text)

            # Clean up the session from memory
            del self._chat_sessions[session_id]

            return {
                "success": True,
                "evaluation": evaluation_data,
                "full_response": response_text
            }
        except Exception as e:
            print(f"Error finalizing evaluation: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_response": response.text if 'response' in locals() else None
            }

    def _parse_structured_evaluation(self, response_text):
        """Parse structured text response into evaluation data"""

        # Default structure
        evaluation_data = {
            "age_appropriateness": {
                "recommended_age_range": "8-12 years",
                "grade_levels": ["grade3", "grade4", "grade5"],
                "complexity_score": 5,
                "reasoning": "Suitable for elementary students"
            },
            "feasibility": {
                "difficulty_level": "intermediate",
                "estimated_time_hours": 4,
                "required_materials": ["basic supplies"],
                "required_skills": ["creativity", "basic research"],
                "feasibility_score": 7
            },
            "evaluation_parameters": {
                "creativity_weight": 30,
                "technical_execution_weight": 25,
                "presentation_quality_weight": 25,
                "adherence_to_brief_weight": 20,
                "specific_criteria": ["originality", "completion"]
            },
            "recommended_credits": {
                "min_credits": 8,
                "max_credits": 15,
                "bonus_criteria": ["early submission", "exceptional quality"]
            },
            "recommended_submission_format": "text",
            "format_reasoning": "Best suits the project requirements",
            "potential_challenges": ["time management", "resource availability"],
            "success_indicators": ["project completion", "learning demonstration"]
        }

        try:
            # Extract age range
            age_match = re.search(r'age range:\s*([^\n]+)', response_text, re.IGNORECASE)
            if age_match:
                evaluation_data["age_appropriateness"]["recommended_age_range"] = age_match.group(1).strip()

            # Extract difficulty level
            difficulty_match = re.search(r'difficulty level:\s*(\w+)', response_text, re.IGNORECASE)
            if difficulty_match:
                evaluation_data["feasibility"]["difficulty_level"] = difficulty_match.group(1).strip().lower()

            # Extract time estimate
            time_match = re.search(r'estimated time:\s*(\d+)', response_text, re.IGNORECASE)
            if time_match:
                evaluation_data["feasibility"]["estimated_time_hours"] = int(time_match.group(1))

            # Extract complexity score
            complexity_match = re.search(r'complexity score.*?(\d+)', response_text, re.IGNORECASE)
            if complexity_match:
                evaluation_data["age_appropriateness"]["complexity_score"] = int(complexity_match.group(1))

            # Extract feasibility score
            feasibility_match = re.search(r'feasibility score.*?(\d+)', response_text, re.IGNORECASE)
            if feasibility_match:
                evaluation_data["feasibility"]["feasibility_score"] = int(feasibility_match.group(1))

            # Extract credits
            min_credits_match = re.search(r'minimum credits:\s*(\d+)', response_text, re.IGNORECASE)
            max_credits_match = re.search(r'maximum credits:\s*(\d+)', response_text, re.IGNORECASE)

            if min_credits_match:
                evaluation_data["recommended_credits"]["min_credits"] = int(min_credits_match.group(1))
            if max_credits_match:
                evaluation_data["recommended_credits"]["max_credits"] = int(max_credits_match.group(1))

            # Extract submission format recommendation
            format_match = re.search(r'recommended format:\s*(\w+)', response_text, re.IGNORECASE)
            if format_match:
                format_value = format_match.group(1).strip().lower()
                if format_value in ['video', 'image', 'url', 'pdf', 'text']:
                    evaluation_data["recommended_submission_format"] = format_value

            # Extract format reasoning
            reasoning_match = re.search(r'format reasoning:\s*([^\n]+)', response_text, re.IGNORECASE)
            if reasoning_match:
                evaluation_data["format_reasoning"] = reasoning_match.group(1).strip()

        except Exception as e:
            print(f"Error parsing structured response: {e}")
            # Return default values if parsing fails

        return evaluation_data

    def evaluate_student_submission(self, project_data, submission_data, file_content=None):
        """Evaluate student submission using structured prompting"""

        model = self.get_model()
        if model is None:
            return {
                "success": False,
                "error": "Gemini service not available"
            }

        evaluation_prompt = f"""
        You are evaluating a student's project submission. Here are the details:

        ORIGINAL PROJECT:
        Title: {project_data.get('title')}
        Description: {project_data.get('description')}
        Required Format: {project_data.get('submission_format', 'text')}

        STUDENT SUBMISSION:
        Description: {submission_data.get('description')}
        Submission Type: {submission_data.get('submission_type')}

        Please evaluate this submission and structure your response as follows:

        OVERALL ASSESSMENT:
        - Overall score (0-100): [score]
        - Quality tier: [exceptional/good/satisfactory/needs_improvement]
        - Meets requirements: [yes/no]

        DETAILED SCORES:
        - Creativity (0-100): [score]
        - Technical execution (0-100): [score]
        - Presentation quality (0-100): [score]
        - Adherence to brief (0-100): [score]

        FEEDBACK:
        - Strengths: [list 2-3 strengths]
        - Areas for improvement: [list 2-3 areas]
        - Specific comments: [detailed feedback]

        RECOMMENDATION:
        - Action: [approve/request_revision/reject]
        - Bonus eligible: [yes/no]
        - Bonus reasoning: [explanation if applicable]

        Be constructive in your feedback and consider this is work by a school student. Give reason for all marks and scores.
        """

        try:
            if file_content and submission_data.get('submission_type') in ['image', 'video']:
                # For image/video submissions, use vision model (same as regular model for 2.0 Flash)
                response = self.vision_model.generate_content([evaluation_prompt, file_content])
            else:
                # For text/URL submissions, use regular model
                response = model.generate_content(evaluation_prompt)

            response_text = response.text

            # Parse structured response
            evaluation_result = self._parse_structured_submission_evaluation(response_text)

            return {
                "success": True,
                "evaluation": evaluation_result,
                "full_response": response_text
            }
        except Exception as e:
            print(f"Error evaluating submission: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_response": response.text if 'response' in locals() else None
            }

    def _parse_structured_submission_evaluation(self, response_text):
        """Parse structured submission evaluation response"""

        # Default evaluation structure
        evaluation_result = {
            "overall_score": 75,
            "parameter_scores": {
                "creativity": 75,
                "technical_execution": 70,
                "presentation_quality": 80,
                "adherence_to_brief": 75
            },
            "meets_requirements": True,
            "quality_tier": "good",
            "feedback": {
                "strengths": ["Good effort", "Creative approach"],
                "areas_for_improvement": ["Could be more detailed"],
                "specific_comments": "Well done overall with room for improvement"
            },
            "recommended_action": "approve",
            "bonus_eligible": False,
            "bonus_reasoning": "Meets standard requirements"
        }

        try:
            # Extract overall score
            overall_match = re.search(r'overall score.*?(\d+)', response_text, re.IGNORECASE)
            if overall_match:
                evaluation_result["overall_score"] = int(overall_match.group(1))

            # Extract quality tier
            quality_match = re.search(r'quality tier:\s*(\w+)', response_text, re.IGNORECASE)
            if quality_match:
                evaluation_result["quality_tier"] = quality_match.group(1).strip().lower()

            # Extract individual scores
            creativity_match = re.search(r'creativity.*?(\d+)', response_text, re.IGNORECASE)
            technical_match = re.search(r'technical execution.*?(\d+)', response_text, re.IGNORECASE)
            presentation_match = re.search(r'presentation quality.*?(\d+)', response_text, re.IGNORECASE)
            adherence_match = re.search(r'adherence to brief.*?(\d+)', response_text, re.IGNORECASE)

            if creativity_match:
                evaluation_result["parameter_scores"]["creativity"] = int(creativity_match.group(1))
            if technical_match:
                evaluation_result["parameter_scores"]["technical_execution"] = int(technical_match.group(1))
            if presentation_match:
                evaluation_result["parameter_scores"]["presentation_quality"] = int(presentation_match.group(1))
            if adherence_match:
                evaluation_result["parameter_scores"]["adherence_to_brief"] = int(adherence_match.group(1))

            # Extract recommendation
            action_match = re.search(r'action:\s*(\w+)', response_text, re.IGNORECASE)
            if action_match:
                evaluation_result["recommended_action"] = action_match.group(1).strip().lower()

            # Extract meets requirements
            meets_match = re.search(r'meets requirements:\s*(yes|no)', response_text, re.IGNORECASE)
            if meets_match:
                evaluation_result["meets_requirements"] = meets_match.group(1).strip().lower() == 'yes'

            # Extract bonus eligibility
            bonus_match = re.search(r'bonus eligible:\s*(yes|no)', response_text, re.IGNORECASE)
            if bonus_match:
                evaluation_result["bonus_eligible"] = bonus_match.group(1).strip().lower() == 'yes'

        except Exception as e:
            print(f"Error parsing submission evaluation: {e}")
            # Return default values if parsing fails

        return evaluation_result

    def process_image_for_evaluation(self, image_file):
        """Process uploaded image for Gemini evaluation"""
        try:
            image = Image.open(image_file)

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if too large (more conservative for free tier)
            max_size = (800, 800)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            return image
        except Exception as e:
            print(f"Error processing image: {e}")
            return None

    def cleanup_expired_sessions(self, max_age_hours=24):
        """Clean up old chat sessions to prevent memory leaks"""
        import time
        current_time = time.time()
        expired_sessions = []

        for session_id, session_data in self._chat_sessions.items():
            if isinstance(session_data, tuple) and len(session_data) > 1:
                session_time = session_data[1]
                if current_time - session_time > max_age_hours * 3600:
                    expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self._chat_sessions[session_id]

        if expired_sessions:
            print(f"Cleaned up {len(expired_sessions)} expired chat sessions")
