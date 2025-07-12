from datetime import datetime
import json


class Submission:
    def __init__(self, id=None, project_id=None, student_id=None,
                 description=None, submission_type='text', file_url=None,
                 status='pending', ai_evaluation=None, admin_feedback=None,
                 submitted_at=None, reviewed_at=None, points_awarded=0):
        self.id = id
        self.project_id = project_id
        self.student_id = student_id
        self.description = description
        self.submission_type = submission_type  # text, image, video, url
        self.file_url = file_url
        self.status = status  # pending, approved, rejected, revision_requested
        self.ai_evaluation = ai_evaluation or {}
        self.admin_feedback = admin_feedback
        self.submitted_at = submitted_at or datetime.utcnow()
        self.reviewed_at = reviewed_at
        self.points_awarded = points_awarded

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'student_id': self.student_id,
            'description': self.description,
            'submission_type': self.submission_type,
            'file_url': self.file_url,
            'status': self.status,
            'ai_evaluation': json.dumps(self.ai_evaluation) if isinstance(self.ai_evaluation,
                                                                          dict) else self.ai_evaluation,
            'admin_feedback': self.admin_feedback,
            'submitted_at': self.submitted_at.isoformat() if isinstance(self.submitted_at,
                                                                        datetime) else self.submitted_at,
            'reviewed_at': self.reviewed_at.isoformat() if isinstance(self.reviewed_at, datetime) else self.reviewed_at,
            'points_awarded': self.points_awarded
        }

    @staticmethod
    def from_dict(data):
        submission = Submission()
        submission.id = data.get('id')
        submission.project_id = data.get('project_id')
        submission.student_id = data.get('student_id')
        submission.description = data.get('description')
        submission.submission_type = data.get('submission_type', 'text')
        submission.file_url = data.get('file_url')
        submission.status = data.get('status', 'pending')
        submission.admin_feedback = data.get('admin_feedback')
        submission.submitted_at = data.get('submitted_at')
        submission.reviewed_at = data.get('reviewed_at')
        submission.points_awarded = data.get('points_awarded', 0)

        # Handle JSON field
        ai_eval = data.get('ai_evaluation')
        if isinstance(ai_eval, str):
            try:
                submission.ai_evaluation = json.loads(ai_eval)
            except:
                submission.ai_evaluation = {}
        else:
            submission.ai_evaluation = ai_eval or {}

        return submission
