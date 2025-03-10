import time
from src.action_handler import register_action
from src.helpers import print_h_bar
import json

categories = [
            "Software Development",
            "Data Science",
            "Web Development",
            "Machine Learning",
            "DevOps",
            "Cloud Computing",
            "Cybersecurity",
            "UI/UX Design",
            "Product Management",
            "Digital Marketing"
        ]

def welcome_message() -> str:
        """Generate the welcome message with trending categories"""
        message = "👋 Welcome! I can help you find your dream job!\n\n"
        message += "🔍 You can search for jobs by:\n"
        message += "1. Entering a search query (e.g., 'Python developer in New York')\n"
        message += "2. Choosing from our trending categories:\n\n"
        
        for i, category in enumerate(categories, 1):
            message += f"   {i}. {category}\n"
            
        message += "\nWhat kind of job are you looking for?"
        return message

def generate_jobs(agent, query: str, is_category: bool = False) -> list:
    """Generate job listings using OpenAI"""
    system_prompt = """You are a job search assistant. Generate 10 realistic job listings based on the search query or category.
    Each job should include:
    - Title
    - Company
    - Location
    - Salary Range
    - Description (2-3 sentences)
    - Requirements (3-4 key points)
    - Application Link (fictional but realistic URL)
    
    Return the results as a JSON array of job objects."""

    prompt = f"{'Category' if is_category else 'Search query'}: {query}\nGenerate relevant job listings."
    
    try:
        response = agent.connections["openai"].generate_text(
            prompt=prompt,
            system_prompt=system_prompt
        )
        return json.loads(response)
    except Exception as e:
        agent.logger.error(f"Error generating jobs: {str(e)}")
        return []

def format_job_listing(job: dict, index: int = None) -> str:
    """Format a job listing for display"""
    prefix = f"{index}. " if index is not None else ""
    return f"""{prefix}🏢 {job['title']} at {job['company']}
📍 {job['location']}
💰 {job['salary_range']}

{job['description']}

Key Requirements:
{''.join(f'• {req}\\n' for req in job['requirements'])}
"""

def format_job_details(job: dict) -> str:
    """Format detailed job information"""
    return f"""📋 Detailed Job Information
======================

🏢 Position: {job['title']}
🏛️ Company: {job['company']}
📍 Location: {job['location']}
💰 Salary Range: {job['salary_range']}

📝 Description:
{job['description']}

🎯 Key Requirements:
{''.join(f'• {req}\\n' for req in job['requirements'])}

🔗 How to Apply:
{job['application_link']}

To go back to the job list, just type "back" or "return".
"""

@register_action("job-prompt")
def job_prompt(agent, **kwargs): # expects user_prompt
    if ("is_first_time" not in agent.state):
        is_first_time = True
    else:
        is_first_time = agent.state["is_first_time"] # False

    if is_first_time:
        print_h_bar()
        agent.logger.info(welcome_message())
        agent.state["is_first_time"] = False
        return True
    else:
        user_prompt = kwargs.get("user_prompt", "").strip()
        if not user_prompt:
            agent.logger.info("Please provide a search query or select a job category.")
            return False

        # System prompt to analyze user input
        system_prompt = """You are a job search assistant. Analyze the user's input and determine if it's:
        1. A search query (e.g., "Python developer in New York")
        2. A category selection (e.g., "Show me software engineering jobs")
        3. A request for job details (e.g., "Show me more about job 3" or "Tell me about the third job")
        4. A request to go back to the list
        5. An unclear/invalid input
        
        Respond with a JSON object containing:
        {
            "type": "search_query|category|details|back|invalid",
            "query": "processed search terms or category",
            "message": "appropriate response message",
            "job_number": null or job number if requesting details
        }"""

        try:
            # Use OpenAI to analyze the input
            response = agent.connections["openai"].generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            response_data = json.loads(response)
            
            # Process the response and take appropriate action
            if response_data["type"] == "search_query":
                # Handle job search
                agent.logger.info(f"🔍 Searching for jobs matching: {response_data['query']}")
                jobs = generate_jobs(agent, response_data['query'])
                agent.state["current_jobs"] = jobs
                
                # Display job listings
                for i, job in enumerate(jobs, 1):
                    agent.logger.info(format_job_listing(job, i))
                
                agent.logger.info("\nTo learn more about a specific job, enter its number or say 'Tell me about job X'")
                return True
                
            elif response_data["type"] == "category":
                # Handle category selection
                category = response_data['query']
                agent.logger.info(f"📂 Showing jobs in category: {category}")
                jobs = generate_jobs(agent, category, is_category=True)
                agent.state["current_jobs"] = jobs
                
                # Display job listings
                for i, job in enumerate(jobs, 1):
                    agent.logger.info(format_job_listing(job, i))
                
                agent.logger.info("\nTo learn more about a specific job, enter its number or say 'Tell me about job X'")
                return True
                
            elif response_data["type"] == "details":
                # Handle job details request
                if "current_jobs" not in agent.state:
                    agent.logger.info("❌ Please search for jobs first before requesting details.")
                    return False
                
                job_number = response_data.get("job_number")
                if not job_number or job_number < 1 or job_number > len(agent.state["current_jobs"]):
                    agent.logger.info("❌ Invalid job number. Please specify a valid job number.")
                    return False
                
                job = agent.state["current_jobs"][job_number - 1]
                agent.logger.info(format_job_details(job))
                return True
                
            elif response_data["type"] == "back":
                # Handle going back to the list
                if "current_jobs" not in agent.state:
                    agent.logger.info("❌ No previous job list to return to. Please start a new search.")
                    return False
                
                agent.logger.info("⬅️ Here's the previous job list:")
                for i, job in enumerate(agent.state["current_jobs"], 1):
                    agent.logger.info(format_job_listing(job, i))
                return True
                
            else:
                # Handle unclear input
                agent.logger.info("❌ I couldn't understand your request. Please try again with a specific job search or category selection.")
                return False

        except Exception as e:
            agent.logger.error(f"Error processing your request: {str(e)}")
            return False


