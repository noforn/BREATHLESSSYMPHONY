import os
import datetime
import re
from tools.tools import Tools

class WebSearch(Tools):
    """
    Web search tool using duckduckgo_search package
    Returns clean search results for the agent to process
    """
    
    def __init__(self):
        super().__init__()
        self.tag = "web_search"
        self.name = "Web Search"
        self.description = "Performs web searches using DuckDuckGo"
        try:
            from core.ui import ui
            self.ui = ui
        except ImportError:
            self.ui = None
        try:
            from duckduckgo_search import DDGS
            self.DDGS = DDGS
            self.ddgs_available = True
        except ImportError:
            self.ddgs_available = False
            if self.ui:
                self.ui.status("duckduckgo_search not installed. Run: pip install duckduckgo_search", "error")

    def handle_builtin_queries(self, query: str) -> str:
        """Handle simple queries with immediate responses"""
        query_lower = query.lower().strip()
        
        if any(phrase in query_lower for phrase in [
            'current date', 'today date', 'what date', 'date today', 'todays date'
        ]):
            today = datetime.datetime.now()
            return f"Current Date: {today.strftime('%A, %B %d, %Y')}"
        
        if any(phrase in query_lower for phrase in [
            'current time', 'what time', 'time now'
        ]):
            now = datetime.datetime.now()
            return f"Current Time: {now.strftime('%I:%M %p')}"
        
        return None

    def search_ddg(self, query: str) -> str:
        """Perform DuckDuckGo search using proven method"""
        if not self.ddgs_available:
            return "Error: duckduckgo_search package not installed"
        
        try:
            if self.ui:
                self.ui.thinking(f"Searching: {query}")
            
            results = self.DDGS().text(
                keywords=query,
                region='wt-wt',
                safesearch='moderate', 
                timelimit='30d',
                max_results=8
            )
            
            if not results:
                return f"No search results found for: {query}"
            
            formatted_results = []
            for i, result in enumerate(results[:5], 1):
                title = result.get('title', 'No title')
                href = result.get('href', 'No URL')
                body = result.get('body', 'No description')
                
                if len(body) > 200:
                    body = body[:200] + "..."
                
                formatted_results.append(
                    f"Result {i}:\n"
                    f"Title: {title}\n"
                    f"URL: {href}\n" 
                    f"Description: {body}"
                )
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            if "429" in str(e):
                error_msg += " (Rate limited - wait before searching again)"
            return error_msg

    def execute(self, blocks: list, safety: bool = False) -> str:
        """Execute web search for given query blocks"""
        if not blocks or not isinstance(blocks, list):
            return "Error: No search query provided"

        output = ""
        for block in blocks:
            query = block.strip()
            
            if not query:
                output += "Error: Empty search query\n"
                continue
            
            builtin_response = self.handle_builtin_queries(query)
            if builtin_response:
                output += f"{builtin_response}\n"
                continue
            
            search_result = self.search_ddg(query)
            output += f"Search results for '{query}':\n{search_result}\n"
        
        return output.strip()

    def execution_failure_check(self, output: str) -> bool:
        """Check if search failed"""
        if not output:
            return True
        
        failure_indicators = ["Error:", "Search failed", "No search results found"]
        success_indicators = ["Current Date:", "Current Time:", "Result 1:"]
        
        has_success = any(indicator in output for indicator in success_indicators)
        has_failure = any(indicator in output for indicator in failure_indicators)
        
        return has_failure and not has_success

    def interpreter_feedback(self, output: str) -> str:
        """Provide feedback to the agent"""
        if not output:
            return "No search output generated"
        
        if self.execution_failure_check(output):
            return f"[failure] Web search failed:\n{output}"
        else:
            return f"[success] Web search completed:\n{output}"