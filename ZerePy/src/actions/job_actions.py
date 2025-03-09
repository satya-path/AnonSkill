import logging
from typing import Dict, Any, List
from src.action_handler import register_action
import json

logger = logging.getLogger("actions.job_actions")

def format_job_listing(job: Dict[str, Any]) -> str:
    """Format a job listing for display"""
    return f"""
🔹 Title: {job.get('title')}
💼 Company: {job.get('company')}
📍 Location: {job.get('location', 'Remote/Unspecified')}
💰 Salary: {job.get('salary', 'Not specified')}
🔗 Link: {job.get('link')}

Description:
{job.get('description', 'No description available')}
"""

@register_action("fetch-jobs")
def handle_fetch_jobs(agent):
    """Fetch and store new job listings"""
    try:
        # Get latest tweets about Web3 jobs
        tweets = agent.perform_action(
            "twitter",
            "search",
            query="#web3jobs OR #cryptojobs OR #blockchainjobs"
        )

        # Process tweets into job listings
        for tweet in tweets:
            # Generate embedding for the tweet
            embedding = agent.perform_action(
                "openai",
                "get-embedding",
                text=tweet['text']
            )

            # Store in vector database
            metadata = {
                'title': tweet.get('title', 'Untitled Position'),
                'company': tweet.get('company', 'Unknown'),
                'location': tweet.get('location', 'Remote/Unspecified'),
                'description': tweet['text'],
                'link': f"https://twitter.com/i/web/status/{tweet['id']}",
                'timestamp': tweet['created_at'],
                'type': 'job'
            }

            agent.perform_action(
                "vectordb",
                "add-item",
                vector=embedding,
                metadata=metadata
            )

        logger.info("✅ Successfully fetched and stored new job listings")
        return True

    except Exception as e:
        logger.error(f"Failed to fetch jobs: {e}")
        return False

@register_action("search-jobs")
def handle_search_jobs(agent, query: str, filters: Dict[str, Any] = None, page: int = 1, per_page: int = 5):
    """Search for jobs with pagination"""
    try:
        # Generate embedding for search query
        query_embedding = agent.perform_action(
            "openai",
            "get-embedding",
            text=query
        )

        # Search vector database
        results = agent.perform_action(
            "vectordb",
            "search",
            query_vector=query_embedding,
            k=page * per_page,  # Get enough results for pagination
            filters=filters
        )

        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_results = results[start_idx:end_idx]

        # Format results
        formatted_results = []
        for job in page_results:
            formatted_job = format_job_listing(job)
            formatted_results.append(formatted_job)

        return {
            'jobs': formatted_results,
            'total': len(results),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(results) + per_page - 1) // per_page
        }

    except Exception as e:
        logger.error(f"Failed to search jobs: {e}")
        return None

@register_action("create-resume-nft")
def handle_create_resume_nft(agent, file_path: str, name: str, description: str):
    """Create NFT from resume or certificate"""
    try:
        # Upload file to IPFS
        ipfs_uri = agent.perform_action(
            "sonic",
            "upload-to-ipfs",
            file_path=file_path,
            name=name,
            description=description
        )

        # Mint NFT
        nft_result = agent.perform_action(
            "sonic",
            "mint-nft",
            token_uri=ipfs_uri,
            name=name,
            description=description
        )

        return {
            'success': True,
            'nft_id': nft_result['token_id'],
            'transaction_hash': nft_result['transaction_hash'],
            'ipfs_uri': ipfs_uri
        }

    except Exception as e:
        logger.error(f"Failed to create resume NFT: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@register_action("list-staking-opportunities")
def handle_list_staking(agent, filters: Dict[str, Any] = None, page: int = 1, per_page: int = 5):
    """List staking opportunities with pagination"""
    try:
        # Search vector database for staking opportunities
        query_embedding = agent.perform_action(
            "openai",
            "get-embedding",
            text="staking opportunity restaking yield farming"
        )

        # Add type filter for staking opportunities
        if filters is None:
            filters = {}
        filters['type'] = 'staking'

        results = agent.perform_action(
            "vectordb",
            "search",
            query_vector=query_embedding,
            k=page * per_page,
            filters=filters
        )

        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_results = results[start_idx:end_idx]

        # Format results
        formatted_results = []
        for opportunity in page_results:
            formatted_opp = f"""
🌟 {opportunity.get('title')}
📈 APY: {opportunity.get('apy', 'Not specified')}
🏦 Platform: {opportunity.get('platform')}
💰 Min Stake: {opportunity.get('min_stake', 'Not specified')}
ℹ️ {opportunity.get('description')}
🔗 {opportunity.get('link')}
"""
            formatted_results.append(formatted_opp)

        return {
            'opportunities': formatted_results,
            'total': len(results),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(results) + per_page - 1) // per_page
        }

    except Exception as e:
        logger.error(f"Failed to list staking opportunities: {e}")
        return None

@register_action("analyze-job")
def handle_analyze_job(agent, job_id: int):
    """Analyze a specific job listing using LLM"""
    try:
        # Get job details
        job = agent.perform_action(
            "vectordb",
            "get-item",
            id=job_id
        )

        # Generate analysis prompt
        prompt = f"""
Please analyze this Web3 job posting and provide:
1. Key requirements
2. Required skills
3. Estimated experience level
4. Potential salary range (if not specified)
5. Tips for applying

Job Details:
{format_job_listing(job)}
"""

        # Get analysis from LLM
        analysis = agent.prompt_llm(prompt)
        return analysis

    except Exception as e:
        logger.error(f"Failed to analyze job: {e}")
        return None 