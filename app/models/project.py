from datetime import datetime, timedelta
import json


class Project:
    def __init__(self, id=None, title=None, description=None, parent_id=None,
                 status='pending', credits=0, evaluation_parameters=None,
                 created_at=None, approved_at=None, claimed_by=None,
                 due_date=None, ai_evaluation=None):
        self.id = id
        self.title = title
        self.description = description
        self.parent_id = parent_id
        self.status = status  # pending, approved, claimed, in_progress, completed, rejected
        self.credits = credits
        self.evaluation_parameters = evaluation_parameters or {}
        self.created_at = created_at or datetime.utcnow()
        self.approved_at = approved_at
        self.claimed_by = claimed_by
        self.due_date = due_date
        self.ai_evaluation = ai_evaluation or {}

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'parent_id': self.parent_id,
            'status': self.status,
            'credits': self.credits,
            'evaluation_parameters': json.dumps(self.evaluation_parameters) if isinstance(self.evaluation_parameters,
                                                                                          dict) else self.evaluation_parameters,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'approved_at': self.approved_at.isoformat() if isinstance(self.approved_at, datetime) else self.approved_at,
            'claimed_by': self.claimed_by,
            'due_date': self.due_date.isoformat() if isinstance(self.due_date, datetime) else self.due_date,
            'ai_evaluation': json.dumps(self.ai_evaluation) if isinstance(self.ai_evaluation,
                                                                          dict) else self.ai_evaluation
        }

    @staticmethod
    def from_dict(data):
        project = Project()
        project.id = data.get('id')
        project.title = data.get('title')
        project.description = data.get('description')
        project.parent_id = data.get('parent_id')
        project.status = data.get('status', 'pending')
        project.credits = data.get('credits', 0)

        # Handle JSON fields
        eval_params = data.get('evaluation_parameters')
        if isinstance(eval_params, str):
            try:
                project.evaluation_parameters = json.loads(eval_params)
            except:
                project.evaluation_parameters = {}
        else:
            project.evaluation_parameters = eval_params or {}

        ai_eval = data.get('ai_evaluation')
        if isinstance(ai_eval, str):
            try:
                project.ai_evaluation = json.loads(ai_eval)
            except:
                project.ai_evaluation = {}
        else:
            project.ai_evaluation = ai_eval or {}

        # Handle datetime fields
        project.created_at = data.get('created_at')
        project.approved_at = data.get('approved_at')
        project.claimed_by = data.get('claimed_by')
        project.due_date = data.get('due_date')

        return project

    def claim_by_student(self, student_id, deadline_days=14):
        """Claim project by student and set deadline"""
        self.claimed_by = student_id
        self.status = 'claimed'
        self.due_date = datetime.utcnow() + timedelta(days=deadline_days)
        return self

    def is_overdue(self):
        """Check if project is overdue"""
        if self.due_date and self.status in ['claimed', 'in_progress']:
            return datetime.utcnow() > datetime.fromisoformat(self.due_date.replace('Z', '+00:00'))
        return False
