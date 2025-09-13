"""
Main ticket processing and assignment orchestrator.
"""
import json
from typing import List, Dict
from .data_loader import DataLoader
from .llm_assigner import LLMAssigner
from .models import Agent, Ticket, Assignment


class TicketProcessor:
    """Main class for processing tickets and generating assignments."""
    
    def __init__(self, dataset_path: str, api_key: str):
        """Initialize the ticket processor."""
        self.data_loader = DataLoader(dataset_path)
        self.llm_assigner = LLMAssigner(api_key)
        self.agents: Dict[str, Agent] = {}
        self.tickets: List[Ticket] = []
        self.assignments: List[Assignment] = []
    
    def initialize(self):
        """Load and initialize agents and tickets from dataset."""
        self.agents, self.tickets = self.data_loader.load_data()
        print(f"Initialized {len(self.agents)} agents and {len(self.tickets)} tickets")
    
    def process_all_tickets(self) -> List[Assignment]:
        """Process all tickets and generate assignments with workload balancing."""
        self.assignments = []
        total_tickets = len(self.tickets)
        max_workload_per_agent = int(total_tickets * 0.11)  # 11% threshold
        
        print(f"Processing {total_tickets} tickets with max {max_workload_per_agent} tickets per agent")
        
        for i, ticket in enumerate(self.tickets, 1):
            print(f"Processing ticket {i}/{len(self.tickets)}: {ticket.ticket_id}")
            
            try:
                # Check if any agents are available
                available_agents = [a for a in self.agents.values() if a.is_available()]
                if not available_agents:
                    print(f"Warning: No available agents for ticket {ticket.ticket_id}")
                    # Create a fallback assignment to the first agent
                    fallback_assignment = self._create_fallback_assignment(ticket)
                    self.assignments.append(fallback_assignment)
                    continue
                
                assignment = self.llm_assigner.assign_ticket(ticket, self.agents, total_tickets)
                self.assignments.append(assignment)
                
                # Update agent workload
                if assignment.assigned_agent_id in self.agents:
                    self.agents[assignment.assigned_agent_id].current_load += 1
                    
                    # Check if agent has reached the 11% threshold
                    if self.agents[assignment.assigned_agent_id].current_load >= max_workload_per_agent:
                        self.agents[assignment.assigned_agent_id].availability_status = "UNAVAILABLE"
                        print(f"Agent {assignment.assigned_agent_id} marked as UNAVAILABLE (workload: {self.agents[assignment.assigned_agent_id].current_load})")
                
            except Exception as e:
                print(f"Error processing ticket {ticket.ticket_id}: {e}")
                # Create a fallback assignment
                fallback_assignment = self._create_fallback_assignment(ticket)
                self.assignments.append(fallback_assignment)
        
        return self.assignments
    
    def _create_fallback_assignment(self, ticket: Ticket) -> Assignment:
        """Create a fallback assignment when LLM fails."""
        # Find the agent with the lowest current load among available agents
        available_agents = [a for a in self.agents.values() if a.is_available()]
        if not available_agents:
            # If no available agents, use the first one (emergency fallback)
            assigned_agent = list(self.agents.values())[0]
        else:
            assigned_agent = min(available_agents, key=lambda a: a.current_load)
        
        return Assignment(
            ticket_id=ticket.ticket_id,
            title=ticket.title,
            assigned_agent_id=assigned_agent.agent_id,
            rationale=f"Fallback assignment to {assigned_agent.name} due to processing error"
        )
    
    def save_assignments(self, output_path: str):
        """Save assignments to JSON file in the required format."""
        output_data = {
            "sample_output": [
                {
                    "ticket_id": assignment.ticket_id,
                    "title": assignment.title,
                    "assigned_agent_id": assignment.assigned_agent_id,
                    "rationale": assignment.rationale
                }
                for assignment in self.assignments
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(output_data, file, indent=2, ensure_ascii=False)
        
        print(f"Assignments saved to {output_path}")
    
    def get_assignment_summary(self) -> Dict:
        """Get a summary of assignments for analysis."""
        agent_assignments = {}
        for assignment in self.assignments:
            agent_id = assignment.assigned_agent_id
            if agent_id not in agent_assignments:
                agent_assignments[agent_id] = []
            agent_assignments[agent_id].append(assignment.ticket_id)
        
        total_tickets = len(self.tickets)
        max_workload = int(total_tickets * 0.11)
        
        # Calculate workload distribution
        workload_distribution = {}
        for agent_id, tickets in agent_assignments.items():
            current_load = len(tickets)
            workload_percentage = (current_load / total_tickets) * 100
            workload_distribution[agent_id] = {
                "tickets": current_load,
                "percentage": round(workload_percentage, 2),
                "status": "OVER_LIMIT" if current_load > max_workload else "WITHIN_LIMIT"
            }
        
        return {
            "total_tickets": total_tickets,
            "total_assignments": len(self.assignments),
            "agents_used": len(agent_assignments),
            "max_workload_per_agent": max_workload,
            "workload_distribution": workload_distribution,
            "assignments_per_agent": {agent_id: len(tickets) for agent_id, tickets in agent_assignments.items()}
        }
