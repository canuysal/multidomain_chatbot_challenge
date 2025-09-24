import requests
from typing import Optional, Dict, Any, List
import json


class ResearchTool:
    """Tool for fetching research information from Semantic Scholar API"""

    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.search_url = f"{self.base_url}/paper/search"

    def search_research(self, topic: str) -> str:
        """
        Search for academic research papers and information on a topic

        Args:
            topic (str): Research topic or subject to search for

        Returns:
            str: Formatted research findings or error message
        """
        try:
            if not topic or not topic.strip():
                return "Please provide a valid research topic."

            topic = topic.strip()

            # Make request to Semantic Scholar API
            params = {
                'query': topic,
                'limit': 5,  # Get top 5 papers
                'fields': 'title,authors,year,abstract,citationCount,url,publicationDate'
            }

            headers = {
                'User-Agent': 'MultiDomainChatbot/1.0 (research-assistant)',
            }

            response = requests.get(self.search_url, params=params, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                return self._format_research_response(data, topic)

            elif response.status_code == 400:
                return f"Invalid search query for '{topic}'. Please try a different search term."

            elif response.status_code == 429:
                return "Research service is temporarily unavailable due to rate limiting. Please try again later."

            elif response.status_code == 500:
                return "Research service is temporarily unavailable. Please try again later."

            else:
                return f"Sorry, I encountered an error while searching for research on '{topic}'. Please try again later."

        except requests.exceptions.Timeout:
            return "The research request timed out. Please try again."

        except requests.exceptions.ConnectionError:
            return "Unable to connect to the research service. Please check your internet connection."

        except requests.exceptions.RequestException as e:
            return f"An error occurred while searching for research: {str(e)}"

        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def _format_research_response(self, data: Dict[Any, Any], topic: str) -> str:
        """
        Format the Semantic Scholar API response into a readable format

        Args:
            data (Dict): Semantic Scholar API response data
            topic (str): Original search topic

        Returns:
            str: Formatted research response
        """
        try:
            papers = data.get('data', [])

            if not papers:
                return f"No research papers found for '{topic}'. Please try a different search term or check the spelling."

            response = f"📚 **Research Results for '{topic}'**\n\n"
            response += f"Found {len(papers)} relevant papers:\n\n"

            for i, paper in enumerate(papers, 1):
                title = paper.get('title', 'Untitled')
                authors = paper.get('authors', [])
                year = paper.get('year')
                abstract = paper.get('abstract', '')
                citations = paper.get('citationCount', 0)
                url = paper.get('url', '')

                response += f"**{i}. {title}**\n"

                # Add authors
                if authors:
                    author_names = [author.get('name', 'Unknown') for author in authors[:3]]
                    if len(authors) > 3:
                        author_names.append(f"... and {len(authors) - 3} others")
                    response += f"👥 *Authors*: {', '.join(author_names)}\n"

                # Add year and citations
                if year:
                    response += f"📅 *Year*: {year}"
                if citations:
                    response += f" | 📊 *Citations*: {citations:,}"
                if year or citations:
                    response += "\n"

                # Add abstract (shortened)
                if abstract:
                    if len(abstract) > 200:
                        abstract = abstract[:197] + "..."
                    response += f"📄 *Abstract*: {abstract}\n"

                # Add URL
                if url:
                    response += f"🔗 [Read Paper]({url})\n"

                response += "\n"

            # Add summary
            total_citations = sum(paper.get('citationCount', 0) for paper in papers)
            response += f"📈 **Summary**: {len(papers)} papers with {total_citations:,} total citations"

            return response.strip()

        except Exception as e:
            return f"Found research information but couldn't format it properly: {str(e)}"

    def get_paper_details(self, paper_id: str) -> str:
        """
        Get detailed information about a specific paper

        Args:
            paper_id (str): Semantic Scholar paper ID

        Returns:
            str: Detailed paper information
        """
        try:
            url = f"{self.base_url}/paper/{paper_id}"
            params = {
                'fields': 'title,authors,year,abstract,citationCount,referenceCount,publicationDate,venue,fieldsOfStudy,url'
            }

            headers = {
                'User-Agent': 'MultiDomainChatbot/1.0 (research-assistant)',
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self._format_paper_details(data)
            else:
                return f"Could not retrieve details for paper ID: {paper_id}"

        except Exception as e:
            return f"Error retrieving paper details: {str(e)}"

    def _format_paper_details(self, paper: Dict[Any, Any]) -> str:
        """Format detailed paper information"""
        try:
            title = paper.get('title', 'Untitled')
            authors = paper.get('authors', [])
            year = paper.get('year')
            abstract = paper.get('abstract', '')
            citations = paper.get('citationCount', 0)
            references = paper.get('referenceCount', 0)
            venue = paper.get('venue', 'Unknown')
            fields = paper.get('fieldsOfStudy', [])
            url = paper.get('url', '')

            response = f"📄 **{title}**\n\n"

            if authors:
                author_names = [author.get('name', 'Unknown') for author in authors]
                response += f"👥 **Authors**: {', '.join(author_names)}\n"

            if year:
                response += f"📅 **Year**: {year}\n"

            if venue:
                response += f"📖 **Venue**: {venue}\n"

            if fields:
                response += f"🏷️ **Fields**: {', '.join(fields)}\n"

            response += f"📊 **Citations**: {citations:,}\n"
            response += f"📚 **References**: {references:,}\n\n"

            if abstract:
                response += f"📄 **Abstract**:\n{abstract}\n\n"

            if url:
                response += f"🔗 [Read Full Paper]({url})"

            return response.strip()

        except Exception as e:
            return f"Error formatting paper details: {str(e)}"


# Create global instance for use in OpenAI service
research_tool = ResearchTool()