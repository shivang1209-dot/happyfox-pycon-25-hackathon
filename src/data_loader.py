"""
Data loading and initialization utilities.
"""
import json
from typing import Dict, List, Tuple
from .models import Agent, Ticket


class DataLoader:
    """Handles loading and parsing of dataset.json."""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.agents: Dict[str, Agent] = {}
        self.tickets: List[Ticket] = []
    
    def load_data(self) -> Tuple[Dict[str, Agent], List[Ticket]]:
        """Load and parse the dataset.json file."""
        with open(self.dataset_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Load agents
        for agent_data in data['agents']:
            agent = Agent(
                agent_id=agent_data['agent_id'],
                name=agent_data['name'],
                skills=agent_data['skills'],
                current_load=agent_data['current_load'],
                availability_status=agent_data['availability_status'],
                experience_level=agent_data['experience_level']
            )
            self.agents[agent.agent_id] = agent
        
        # Load tickets
        for ticket_data in data['tickets']:
            ticket = Ticket(
                ticket_id=ticket_data['ticket_id'],
                title=ticket_data['title'],
                description=ticket_data['description'],
                creation_timestamp=ticket_data['creation_timestamp']
            )
            self.tickets.append(ticket)
        
        return self.agents, self.tickets
    
    def get_agents_summary(self) -> str:
        """Get a formatted summary of all agents for LLM context."""
        summary = "Available Agents:\n"
        for agent in self.agents.values():
            if agent.is_available():
                skills_str = ", ".join([f"{skill}: {score}" for skill, score in agent.skills.items()])
                summary += f"- {agent.name} ({agent.agent_id}): Skills: {skills_str}, Current Load: {agent.current_load}, Experience: {agent.experience_level}\n"
        return summary
