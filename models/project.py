from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Project:
    id: str
    title: str
    description: str
    budget: float
    currency: str = 'INR'
    deadline: str
    status: str  # 'open', 'in_progress', 'completed', 'disputed'
    ideator_id: str
    executor_id: Optional[str] = None
    ai_feasibility_score: float = 0.0
    milestones: List[dict] = None
    applications: List[dict] = None
    created_at: str = None
    category: str = 'general' 