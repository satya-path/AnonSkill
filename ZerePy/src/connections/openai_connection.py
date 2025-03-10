import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv, set_key
from openai import OpenAI
from src.connections.base_connection import BaseConnection, Action, ActionParameter

logger = logging.getLogger("connections.openai_connection")

class OpenAIConnectionError(Exception):
    """Base exception for OpenAI connection errors"""
    pass

class OpenAIConfigurationError(OpenAIConnectionError):
    """Raised when there are configuration/credential issues"""
    pass

class OpenAIAPIError(OpenAIConnectionError):
    """Raised when OpenAI API requests fail"""
    pass

class OpenAIConnection(BaseConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def is_llm_provider(self) -> bool:
        return True

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate OpenAI configuration from JSON"""
        required_fields = ["model"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")
            
        # Validate model exists (will be checked in detail during configure)
        if not isinstance(config["model"], str):
            raise ValueError("model must be a string")
            
        return config

    def register_actions(self) -> None:
        """Register available OpenAI actions"""
        self.actions = {
            "generate-text": Action(
                name="generate-text",
                parameters=[
                    ActionParameter("prompt", True, str, "The input prompt for text generation"),
                    ActionParameter("system_prompt", True, str, "System prompt to guide the model"),
                    ActionParameter("model", False, str, "Model to use for generation")
                ],
                description="Generate text using OpenAI models"
            ),
            "check-model": Action(
                name="check-model",
                parameters=[
                    ActionParameter("model", True, str, "Model name to check availability")
                ],
                description="Check if a specific model is available"
            ),
            "list-models": Action(
                name="list-models",
                parameters=[],
                description="List all available OpenAI models"
            ),
            "parse-input": Action(
                name="parse-input",
                parameters=[
                    ActionParameter("user_input", True, str, "User's input text to classify")
                ],
                description="Classify user input into predefined job-related actions"
            ),
            "find-jobs": Action(
                name="find-jobs",
                parameters=[
                    ActionParameter("search_query", True, str, "Job search criteria"),
                    ActionParameter("location", False, str, "Job location preference"),
                    ActionParameter("job_type", False, str, "Type of job (full-time, part-time, etc)")
                ],
                description="Search for jobs based on user criteria using ChatGPT"
            ),
            "view-job": Action(
                name="view-job",
                parameters=[
                    ActionParameter("job_id", True, str, "Unique identifier for the job"),
                    ActionParameter("company", True, str, "Company name")
                ],
                description="Fetch detailed information about a specific job"
            ),
            "apply-to-job": Action(
                name="apply-to-job",
                parameters=[
                    ActionParameter("job_id", True, str, "Unique identifier for the job"),
                    ActionParameter("company", True, str, "Company name")
                ],
                description="Get the application link for a specific job"
            ),
            "show-default-msg": Action(
                name="show-default-msg",
                parameters=[],
                description="Return a default message for invalid inputs"
            )
        }

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client"""
        if not self._client:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise OpenAIConfigurationError("OpenAI API key not found in environment")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def configure(self) -> bool:
        """Sets up OpenAI API authentication"""
        logger.info("\n🤖 OPENAI API SETUP")

        if self.is_configured():
            logger.info("\nOpenAI API is already configured.")
            response = input("Do you want to reconfigure? (y/n): ")
            if response.lower() != 'y':
                return True

        logger.info("\n📝 To get your OpenAI API credentials:")
        logger.info("1. Go to https://platform.openai.com/account/api-keys")
        logger.info("2. Create a new project or open an existing one.")
        logger.info("3. In your project settings, navigate to the API keys section and create a new API key")
        
        api_key = input("\nEnter your OpenAI API key: ")

        try:
            if not os.path.exists('.env'):
                with open('.env', 'w') as f:
                    f.write('')

            set_key('.env', 'OPENAI_API_KEY', api_key)
            
            # Validate the API key by trying to list models
            client = OpenAI(api_key=api_key)
            client.models.list()

            logger.info("\n✅ OpenAI API configuration successfully saved!")
            logger.info("Your API key has been stored in the .env file.")
            return True

        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False

    def is_configured(self, verbose = False) -> bool:
        """Check if OpenAI API key is configured and valid"""
        try:
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return False

            client = OpenAI(api_key=api_key)
            client.models.list()
            return True
            
        except Exception as e:
            if verbose:
                logger.debug(f"Configuration check failed: {e}")
            return False

    def generate_text(self, prompt: str, system_prompt: str, model: str = None, **kwargs) -> str:
        """Generate text using OpenAI models"""
        try:
            client = self._get_client()
            
            # Use configured model if none provided
            if not model:
                model = self.config["model"]

            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )

            return completion.choices[0].message.content
            
        except Exception as e:
            raise OpenAIAPIError(f"Text generation failed: {e}")

    def check_model(self, model, **kwargs):
        try:
            client = self._get_client()
            try:
                client.models.retrieve(model=model)
                # If we get here, the model exists
                return True
            except Exception:
                return False
        except Exception as e:
            raise OpenAIAPIError(e)

    def list_models(self, **kwargs) -> None:
        """List all available OpenAI models"""
        try:
            client = self._get_client()
            response = client.models.list().data
            
            fine_tuned_models = [
                model for model in response 
                if model.owned_by in ["organization", "user", "organization-owner"]
            ]

            logger.info("\nGPT MODELS:")
            logger.info("1. gpt-3.5-turbo")
            logger.info("2. gpt-4")
            logger.info("3. gpt-4-turbo")
            logger.info("4. gpt-4o")
            logger.info("5. gpt-4o-mini")
            
            if fine_tuned_models:
                logger.info("\nFINE-TUNED MODELS:")
                for i, model in enumerate(fine_tuned_models):
                    logger.info(f"{i+1}. {model.id}")
                    
        except Exception as e:
            raise OpenAIAPIError(f"Listing models failed: {e}")

    def parse_input(self, user_input: str, **kwargs) -> dict:
        """Classify user input into predefined job-related actions and extract relevant information"""
        try:
            # First, determine the action type
            action_system_prompt = """You are a job search assistant. Classify the user's input into one of these categories:
            - find_jobs: When user wants to search for jobs
            - view_job: When user wants to view details of a specific job
            - apply_to_job: When user wants to apply to a specific job
            - get_default_msg: When the input doesn't match any of the above
            Only respond with one of these exact categories, nothing else."""

            action_type = self.generate_text(
                prompt=user_input,
                system_prompt=action_system_prompt,
                model=self.config["model"]
            ).strip()

            # Based on action type, get additional information
            if action_type == "find_jobs":
                refine_system_prompt = """You are a job search assistant. Given the user's job search query, 
                create a refined, professional search query. Extract location and job type if mentioned.
                Return a JSON object with these fields:
                {
                    "search_query": "refined search terms",
                    "location": "location if specified, or None",
                    "job_type": "job type if specified (full-time, part-time, contract, etc), or None"
                }"""
                
                refined_info = self.generate_text(
                    prompt=user_input,
                    system_prompt=refine_system_prompt,
                    model=self.config["model"]
                )
                
                return {
                    "action": "find_jobs",
                    "parameters": eval(refined_info)
                }

            elif action_type in ["view_job", "apply_to_job"]:
                extract_system_prompt = """You are a job search assistant. From the user's input, extract:
                1. Job Location (if mentioned)
                2. Company name (if mentioned)
                3. Brief job description or title (if mentioned)
                Return a JSON object with these fields:
                {
                    "job_location": "extracted job location or None",
                    "company": "extracted company name or None",
                    "description": "brief job description/title or None"
                }"""
                
                job_info = self.generate_text(
                    prompt=user_input,
                    system_prompt=extract_system_prompt,
                    model=self.config["model"]
                )
                
                return {
                    "action": action_type,
                    "parameters": eval(job_info)
                }

            else:
                return {
                    "action": "show_default_msg",
                    "parameters": {}
                }

        except Exception as e:
            raise OpenAIAPIError(f"Input parsing failed: {e}")

    def find_jobs(self, search_query: str, location: str = None, job_type: str = None, **kwargs) -> str:
        """Search for jobs based on user criteria"""
        try:
            location_str = f" in {location}" if location else ""
            type_str = f" {job_type}" if job_type else ""
            
            system_prompt = """You are a job search assistant. Search for real jobs and provide a concise list of 5 relevant positions.
            For each job include:
            1. Job ID (generate a unique identifier)
            2. Company name
            3. Job title
            4. Location
            5. Brief description (2-3 lines)
            Format the response in a clear, readable way."""

            search_prompt = f"Find{type_str} jobs matching '{search_query}'{location_str}. Provide real, current job listings."
            
            return self.generate_text(
                prompt=search_prompt,
                system_prompt=system_prompt,
                model=self.config["model"]
            )
        except Exception as e:
            raise OpenAIAPIError(f"Job search failed: {e}")

    def view_job(self, description: str, company: str, **kwargs) -> str:
        """Fetch detailed information about a specific job"""
        try:
            system_prompt = """You are a job search assistant. Provide detailed information about the specified job.
            Include:
            1. Full job description
            2. Required qualifications
            3. Benefits and perks
            4. Company information
            5. Work culture and environment
            Format the response in a clear, structured way."""

            search_prompt = f"Show detailed information for job with the following description at {company}: {description}."
            
            return self.generate_text(
                prompt=search_prompt,
                system_prompt=system_prompt,
                model=self.config["model"]
            )
        except Exception as e:
            raise OpenAIAPIError(f"Job view failed: {e}")

    def apply_to_job(self, description: str, company: str, **kwargs) -> str:
        """Get the application link for a specific job"""
        try:
            system_prompt = """You are a job search assistant. Provide the application process and link for the specified job.
            Include:
            1. Direct application link if available
            2. Alternative application methods if direct link isn't available
            3. Any specific application instructions
            Be concise and practical."""

            search_prompt = f"Get application information for job with the following description at {company}: {description}."
            
            return self.generate_text(
                prompt=search_prompt,
                system_prompt=system_prompt,
                model=self.config["model"]
            )
        except Exception as e:
            raise OpenAIAPIError(f"Job application retrieval failed: {e}")

    def show_default_msg(self, **kwargs) -> str:
        """Return a default message for invalid inputs"""
        return """Here's what you can do:
1. Search for jobs: "Find software developer jobs in New York"
2. View job details: "Show me more about [job ID]"
3. Get application link: "How do I apply for [job ID]"
Please try again with one of these formats."""

    def perform_action(self, action_name: str, kwargs) -> Any:
        """Execute a Twitter action with validation"""
        if action_name not in self.actions:
            raise KeyError(f"Unknown action: {action_name}")

        action = self.actions[action_name]
        errors = action.validate_params(kwargs)
        if errors:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")

        # Call the appropriate method based on action name
        method_name = action_name.replace('-', '_')
        method = getattr(self, method_name)
        return method(**kwargs)
