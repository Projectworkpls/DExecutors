from datetime import datetime, timedelta
import json

# Robust ISO 8601 string parser with fallback (requires python-dateutil)
try:
    from dateutil.parser import isoparse
except ImportError:
    def isoparse(dt):
        # basic fallback for simple ISO8601; not as robust as dateutil
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))

def safe_parse(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt
    try:
        return isoparse(dt.replace("Z", "+00:00")) if isinstance(dt, str) else None
    except Exception:
        return None

class Project:
    def __init__(
        self,
        id=None,
        title=None,
        description=None,
        parent_id=None,
        status='pending',
        credits=0,
        evaluation_parameters=None,
        created_at=None,
        approved_at=None,
        claimed_by=None,
        due_date=None,
        ai_evaluation=None,
        submission_format=None,
        target_age=None,
        admin_notes=None,
        approved_by=None,
        claimed_at=None,
        updated_at=None,
        suggested_credits=None
    ):
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
        self.submission_format = submission_format or 'text'
        self.target_age = target_age
        self.admin_notes = admin_notes
        self.approved_by = approved_by
        self.claimed_at = claimed_at
        self.updated_at = updated_at
        self.suggested_credits = suggested_credits

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'parent_id': self.parent_id,
            'status': self.status,
            'credits': self.credits,
            'evaluation_parameters': json.dumps(self.evaluation_parameters) if isinstance(self.evaluation_parameters, dict) else self.evaluation_parameters,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'approved_at': self.approved_at.isoformat() if isinstance(self.approved_at, datetime) else self.approved_at,
            'claimed_by': self.claimed_by,
            'due_date': self.due_date.isoformat() if isinstance(self.due_date, datetime) else self.due_date,
            'ai_evaluation': json.dumps(self.ai_evaluation) if isinstance(self.ai_evaluation, dict) else self.ai_evaluation,
            'submission_format': self.submission_format,
            'target_age': self.target_age,
            'admin_notes': self.admin_notes,
            'approved_by': self.approved_by,
            'claimed_at': self.claimed_at.isoformat() if isinstance(self.claimed_at, datetime) else self.claimed_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'suggested_credits': self.suggested_credits
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
        project.submission_format = data.get('submission_format', 'text')
        project.target_age = data.get('target_age')
        project.admin_notes = data.get('admin_notes')
        project.approved_by = data.get('approved_by')
        project.suggested_credits = data.get('suggested_credits')

        # Parse JSON fields
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

        # Parse datetime fields
        project.created_at = safe_parse(data.get('created_at'))
        project.approved_at = safe_parse(data.get('approved_at'))
        project.claimed_at = safe_parse(data.get('claimed_at'))
        project.updated_at = safe_parse(data.get('updated_at'))
        project.due_date = safe_parse(data.get('due_date'))

        # Other direct
        project.claimed_by = data.get('claimed_by')

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
            now = datetime.utcnow()
            if isinstance(self.due_date, str):
                try:
                    due_dt = safe_parse(self.due_date)
                except Exception:
                    return False
            else:
                due_dt = self.due_date
            return due_dt and now > due_dt
        return False
