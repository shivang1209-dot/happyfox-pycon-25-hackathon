"""
LLM-based ticket assignment using strands library.
"""
from typing import Dict, List
from strands import Agent as StrandsAgent
from strands.models.openai import OpenAIModel
from .models import Agent, Ticket, Assignment


class LLMAssigner:
    """Handles ticket assignment using LLM via strands library."""
    
    def __init__(self, api_key: str):
        """Initialize the LLM assigner with OpenAI API key."""
        model = OpenAIModel(
            client_args={"api_key": api_key},
            model_id="gpt-4o",
            params={"max_tokens": 1000, "temperature": 0.3}
        )
        self.agent = StrandsAgent(model=model)
    
    def assign_ticket(self, ticket: Ticket, agents: Dict[str, Agent], total_tickets: int) -> Assignment:
        """Assign a ticket to the best available agent using LLM with workload balancing."""
        
        # Create context for the LLM
        agents_context = self._create_agents_context(agents, total_tickets)
        ticket_context = self._create_ticket_context(ticket)
        
        prompt = f"""
You are an expert IT support manager. Your task is to assign support tickets to the most suitable agent based on their skills, current workload, and experience.

{ticket_context}

{agents_context}

IMPORTANT WORKLOAD BALANCING RULES:
- NEVER assign tickets to agents with availability_status "UNAVAILABLE"
- Consider workload distribution: if a less technical agent has much lower workload than the most skilled agent, prefer the less technical one
- Balance between skill match and workload fairness
- Maximum workload per agent should not exceed 11% of total tickets

Based on the ticket requirements and agent capabilities, select the BEST agent for this ticket. Consider:
1. Availability status (UNAVAILABLE agents are excluded)
2. Skill match (important but not absolute)
3. Current workload (lower is better, especially for workload balancing)
4. Experience level

Respond with ONLY the agent_id of the best agent (e.g., "agent_001"). Do not include any other text.
"""
        
        # Get assignment from LLM
        response = self.agent(prompt)
        assigned_agent_id = str(response).strip()
        
        # Validate the response
        if assigned_agent_id not in agents:
            # Fallback to first available agent if LLM returns invalid ID
            available_agents = [a for a in agents.values() if a.is_available()]
            if available_agents:
                assigned_agent_id = available_agents[0].agent_id
            else:
                raise ValueError("No available agents found")
        
        assigned_agent = agents[assigned_agent_id]
        
        # Check if agent is available
        if not assigned_agent.is_available():
            # Find next best available agent
            available_agents = [a for a in agents.values() if a.is_available()]
            if available_agents:
                assigned_agent_id = available_agents[0].agent_id
                assigned_agent = agents[assigned_agent_id]
            else:
                raise ValueError("No available agents found")
        
        # Create rationale
        rationale = self._create_rationale(ticket, assigned_agent, agents)
        
        return Assignment(
            ticket_id=ticket.ticket_id,
            title=ticket.title,
            assigned_agent_id=assigned_agent_id,
            rationale=rationale
        )
    
    def _create_agents_context(self, agents: Dict[str, Agent], total_tickets: int) -> str:
        """Create context string for all available agents with workload information."""
        max_workload = int(total_tickets * 0.11)  # 11% threshold
        
        context = f"Available Agents (Max workload per agent: {max_workload} tickets):\n"
        for agent in agents.values():
            if agent.is_available():
                skills_str = ", ".join([f"{skill}: {score}" for skill, score in agent.skills.items()])
                workload_status = "AT LIMIT" if agent.current_load >= max_workload else f"{agent.current_load}/{max_workload}"
                context += f"- {agent.name} ({agent.agent_id}): Skills: {skills_str}, Current Load: {workload_status}, Experience: {agent.experience_level}\n"
            else:
                context += f"- {agent.name} ({agent.agent_id}): UNAVAILABLE (workload exceeded)\n"
        return context
    
    def _create_ticket_context(self, ticket: Ticket) -> str:
        """Create context string for a ticket."""
        return f"""
Ticket Details:
- ID: {ticket.ticket_id}
- Title: {ticket.title}
- Description: {ticket.description}
"""
    
    def _create_rationale(self, ticket: Ticket, assigned_agent: Agent, all_agents: Dict[str, Agent]) -> str:
        """Create a rationale for the assignment."""
        # Find relevant skills for this ticket
        relevant_skills = self._extract_relevant_skills(ticket)
        
        skill_matches = []
        for skill in relevant_skills:
            score = assigned_agent.get_skill_score(skill)
            if score > 0:
                skill_matches.append(f"{skill} ({score})")
        
        rationale = f"Assigned to {assigned_agent.name} ({assigned_agent.agent_id})"
        
        if skill_matches:
            rationale += f" based on their expertise in {', '.join(skill_matches)}"
        
        rationale += f", current workload of {assigned_agent.current_load}, and experience level of {assigned_agent.experience_level}."
        
        return rationale
    
    def _extract_relevant_skills(self, ticket: Ticket) -> List[str]:
        """Extract relevant skill keywords from ticket title and description."""
        text = f"{ticket.title} {ticket.description}".lower()
        
        # Map common IT terms to skill names
        skill_mapping = {
            'vpn': 'VPN_Troubleshooting',
            'network': 'Networking',
            'windows': 'Windows_OS',
            'server': 'Windows_Server_2022',
            'active directory': 'Active_Directory',
            'email': 'Microsoft_365',
            'outlook': 'Microsoft_365',
            'hardware': 'Hardware_Diagnostics',
            'laptop': 'Laptop_Repair',
            'printer': 'Printer_Troubleshooting',
            'security': 'Network_Security',
            'firewall': 'Firewall_Configuration',
            'database': 'Database_SQL',
            'sql': 'Database_SQL',
            'cloud': 'Cloud_AWS',
            'azure': 'Cloud_Azure',
            'aws': 'Cloud_AWS',
            'linux': 'Linux_Administration',
            'mac': 'Mac_OS',
            'voip': 'Voice_VoIP',
            'phone': 'Voice_VoIP',
            'antivirus': 'Antivirus_Malware',
            'malware': 'Antivirus_Malware',
            'phishing': 'Phishing_Analysis',
            'sharepoint': 'SharePoint_Online',
            'powerbi': 'PowerBI_Tableau',
            'tableau': 'PowerBI_Tableau',
            'api': 'API_Troubleshooting',
            'web': 'Web_Server_Apache_Nginx',
            'dns': 'DNS_Configuration',
            'ssl': 'SSL_Certificates',
            'sso': 'Identity_Management',
            'saml': 'Identity_Management',
            'saas': 'SaaS_Integrations',
            'endpoint': 'Endpoint_Management',
            'mobile': 'Endpoint_Management',
            'virtualization': 'Virtualization_VMware',
            'vmware': 'Virtualization_VMware',
            'docker': 'Kubernetes_Docker',
            'kubernetes': 'Kubernetes_Docker',
            'devops': 'DevOps_CI_CD',
            'ci/cd': 'DevOps_CI_CD',
            'python': 'Python_Scripting',
            'powershell': 'PowerShell_Scripting',
            'monitoring': 'Network_Monitoring',
            'switch': 'Switch_Configuration',
            'routing': 'Routing_Protocols',
            'cisco': 'Cisco_IOS',
            'audit': 'Security_Audits',
            'siem': 'SIEM_Logging',
            'etl': 'ETL_Processes',
            'warehouse': 'Data_Warehousing',
            'apache': 'Web_Server_Apache_Nginx',
            'nginx': 'Web_Server_Apache_Nginx'
        }
        
        relevant_skills = []
        for keyword, skill in skill_mapping.items():
            if keyword in text:
                relevant_skills.append(skill)
        
        return relevant_skills
