"""
Configuration settings for the ticket assignment system.
"""
import os
import dotenv


dotenv.load_dotenv()
# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"
OPENAI_MAX_TOKENS = 1000
OPENAI_TEMPERATURE = 0.3

# File paths
DATASET_PATH = "dataset.json"
OUTPUT_PATH = "output_result.json"

# Processing settings
BATCH_SIZE = 1  # Process one ticket at a time for better LLM context
MAX_RETRIES = 3  # Maximum retries for failed assignments

