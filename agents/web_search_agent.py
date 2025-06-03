import asyncio
from agents.base_agent import Agent
from tools.web_search import WebSearch
from core.memory import Memory
import datetime

now = datetime.datetime.now()

class WebSearchAgent(Agent):
    """
    Web search agent that finds information online and returns results.
    Follows the same simple pattern as FileAgent and ReconAgent.
    """
    
    def __init__(self, name, prompt_path, provider, work_dir, verbose=False):
        super().__init__(name, prompt_path, provider, verbose)
        
        self.work_dir = work_dir
        self.role = "web_search"
        self.type = "web_search_agent"
        
        # Import UI for status messages
        try:
            from core.ui import ui
            self.ui = ui
        except ImportError:
            self.ui = None
        
        # Add web search tool
        try:
            self.add_tool("web_search", WebSearch())
            if self.ui:
                self.ui.system_message(f"WebSearchAgent initialized: web_search tool ready")
        except Exception as e:
            if self.ui:
                self.ui.status(f"WebSearchAgent: Failed to add tools: {e}", "error")
            else:
                print(f"WebSearchAgent: Failed to add tools: {e}")
        
        # Initialize memory
        self.memory = Memory(self.system_prompt)
    
    async def process(self, prompt):
        """
        Process web search requests with retry logic.
        Simple pattern: get query, search, return results.
        """
        exec_success = False
        
        # Enhanced prompt with search context
        enhanced_prompt = f"""{prompt}

Current time: {now.strftime("%Y-%m-%d %H:%M:%S")}

For web searches, use web_search blocks:

```web_search
your search query
```

Examples:
- Current information:
  ```web_search
  latest AI developments 2025
  ```

- Research topics:
  ```web_search
  cybersecurity trends
  ```

- Quick facts:
  ```web_search
  python programming tutorial
  ```

Always explain what you're searching for and provide clear summaries of the results."""

        self.memory.push('user', enhanced_prompt)
        
        retry_count = 0
        max_retries = 3
        all_results = []
        
        # Main execution loop with retry logic
        while not exec_success and not self.stop and retry_count < max_retries:
            self.status_message = "Searching the web..."
            if self.ui and retry_count > 0:
                self.ui.thinking(f"Search retry {retry_count}")
            
            # Get LLM response
            response = self.provider.respond(self.memory.get(), self.verbose)
            
            # Extract reasoning and clean answer
            self.last_reasoning = self.extract_reasoning_text(response)
            clean_answer = self.remove_reasoning_text(response)
            
            # Store response in memory
            self.memory.push('assistant', clean_answer, auto_add_to_scope=False)
            
            # Execute search tools
            exec_success, feedback = self.execute_modules(response)
            
            # Store search results
            if exec_success and feedback and "[success]" in feedback:
                # Extract actual search results from feedback
                search_output = feedback.split(":\n", 1)[1] if ":\n" in feedback else feedback
                all_results.append(search_output)
            
            if not exec_success and feedback:
                # Add retry feedback
                retry_feedback = f"The search failed: {feedback}. Try a different search approach or simpler query."
                self.memory.push('user', retry_feedback, auto_add_to_scope=False)
                retry_count += 1
                if self.ui:
                    self.ui.status(f"Search failed, retrying... ({retry_count}/{max_retries})", "warning")
            else:
                # Build final answer with search results
                if all_results:
                    base_answer = self.remove_blocks(clean_answer)
                    self.last_answer = f"{base_answer}\n\nSearch Results:\n" + "\n".join(all_results)
                else:
                    self.last_answer = self.remove_blocks(clean_answer)
        
        if retry_count >= max_retries:
            error_msg = "Web search failed after multiple attempts. Please try simpler search terms."
            if self.ui:
                self.ui.status("Max search retries reached", "error")
            self.last_answer = error_msg
        
        self.status_message = "Ready"
        return self.last_answer