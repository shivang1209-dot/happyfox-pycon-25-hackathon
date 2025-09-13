"""
Data models for agents and tickets.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Agent:
    """Represents a support agent with their skills and availability."""
    agent_id: str
    name: str
    skills: Dict[str, int]
    current_load: int
    availability_status: str
    experience_level: int
    
    def get_skill_score(self, skill_name: str) -> int:
        """Get skill score for a specific skill, returns 0 if skill doesn't exist."""
        return self.skills.get(skill_name, 0)
    
    def is_available(self) -> bool:
        """Check if agent is available for new tickets."""
        return self.availability_status == "Available"


@dataclass
class Ticket:
    """Represents a support ticket."""
    ticket_id: str
    title: str
    description: str
    creation_timestamp: int
    
    def get_creation_datetime(self) -> datetime:
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(self.creation_timestamp)


@dataclass
class Assignment:
    """Represents a ticket assignment to an agent."""
    ticket_id: str
    title: str
    assigned_agent_id: str
    rationale: str
