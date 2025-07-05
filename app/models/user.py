from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: str
    email: str
    username: str
    user_type: str  # 'ideator', 'executor', 'both'
    reputation_xp: int = 0
    level: int = 1
    total_projects: int = 0
    success_rate: float = 0.0
    created_at: str = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None 