"""
Main entry point for the PyCon25 Hackathon: Intelligent Support Ticket Assignment System.
"""
import os
import sys
from dotenv import load_dotenv
from src.ticket_processor import TicketProcessor


def main():
    """Main function to run the ticket assignment system."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Configuration
    dataset_path = "dataset.json"
    output_path = "output_result.json"
    
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key in the .env file or as an environment variable")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Check if dataset exists
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset file '{dataset_path}' not found")
        sys.exit(1)
    
    try:
        # Initialize the ticket processor
        processor = TicketProcessor(dataset_path, api_key)
        
        # Load data
        print("Loading dataset...")
        processor.initialize()
        
        # Process all tickets
        print("Processing tickets and generating assignments...")
        assignments = processor.process_all_tickets()
        
        # Save results
        print("Saving assignments...")
        processor.save_assignments(output_path)
        
        # Display summary
        summary = processor.get_assignment_summary()
        print("\n" + "="*60)
        print("ASSIGNMENT SUMMARY")
        print("="*60)
        print(f"Total tickets processed: {summary['total_tickets']}")
        print(f"Total assignments created: {summary['total_assignments']}")
        print(f"Number of agents used: {summary['agents_used']}")
        print(f"Max workload per agent: {summary['max_workload_per_agent']} tickets (11% threshold)")
        
        print("\nWorkload Distribution:")
        for agent_id, workload_info in summary['workload_distribution'].items():
            status_icon = "⚠️" if workload_info['status'] == "OVER_LIMIT" else "✅"
            print(f"  {status_icon} {agent_id}: {workload_info['tickets']} tickets ({workload_info['percentage']}%) - {workload_info['status']}")
        
        print(f"\nResults saved to: {output_path}")
        print("="*60)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
