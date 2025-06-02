import asyncio
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Adjust imports based on your project structure
# Assuming 'agents' and 'core' are top-level or in PYTHONPATH
from agents.web_search_agent import WebSearchAgent
from core.memory import Memory, ScopeManager
from tools.web_search import WebSearch # Needed for mocking its methods

class TestWebSearchAgentScope(unittest.TestCase):

    @patch('tools.web_search.WebSearch.search_ddg')
    async def run_test_process(self, mock_search_ddg):
        """Helper async function to run the agent's process method."""
        # 1. Initialize the WebSearchAgent
        # Mock provider for WebSearchAgent initialization
        mock_provider = MagicMock()
        mock_provider.respond = MagicMock()

        agent = WebSearchAgent(
            name="TestWebSearchAgent",
            prompt_path="prompts/web_search_agent.txt", # Provide a dummy path or ensure it exists
            provider=mock_provider,
            work_dir="." # Provide a dummy work_dir
        )

        # Ensure the agent has a UI mock if it tries to use it
        agent.ui = MagicMock()

        # 2. Simulate WebSearchAgent.process with a search query
        # Mock the search_ddg method to return predefined results
        mock_search_results = [
            {"title": "News Example", "url": "http://example-news.com", "description": "Latest news."},
            {"title": "Blog Example", "url": "http://another-blog.org", "description": "Tech blog."},
            {"title": "Secure Site", "url": "https://secure-example.net", "description": "Secure content."}
        ]
        mock_search_ddg.return_value = mock_search_results

        # The agent's process method expects a string prompt that will contain the search query
        # The agent internally constructs the ```web_search block.
        # We need to mock the provider's response to include this block.
        
        # Simulate the LLM response that would trigger the web_search tool
        llm_response_with_search_block = """
        I need to find information about 'latest cybersecurity news'.
        ```web_search
        latest cybersecurity news
        ```
        Here are the results I found.
        """
        mock_provider.respond.return_value = llm_response_with_search_block

        # Call the process method
        search_query_prompt = "Find the latest cybersecurity news."
        await agent.process(search_query_prompt)

        # 3. After the process method completes, inspect the ScopeManager's domains list.
        # The domains that might be extracted by a *normal* (non-search-result) push
        # would be from the `search_query_prompt` if it contained domains.
        # The key is that "example-news.com" etc. from search *results* should NOT be added.
        
        current_scope_domains = agent.memory.scope.domains
        print(f"Domains in scope: {current_scope_domains}")

        # 4. Assert that the domains from the mocked search results are NOT present in the scope.
        domains_from_search_results = ["example-news.com", "another-blog.org", "secure-example.net"]
        
        found_undesired_domain = False
        for domain in domains_from_search_results:
            if domain in current_scope_domains:
                print(f"FAILURE: Domain '{domain}' from search results was found in scope.")
                found_undesired_domain = True
        
        self.assertFalse(found_undesired_domain, "Domains from search results should not be in scope.")

        if not found_undesired_domain:
            print("SUCCESS: Domains from search results were NOT added to the scope.")
        else:
            print("FAILURE: Some domains from search results were added to the scope.")
            
        print(f"Final scope summary:\n{agent.memory.scope.get_scope_summary()}")

    def test_web_search_scope_behavior(self):
        """Synchronous wrapper for the async test."""
        asyncio.run(self.run_test_process())

    def test_explicit_domain_addition_to_scope(self):
        """Tests that domains are added to scope when auto_add_to_scope is True (default)."""
        print("\nRunning test_explicit_domain_addition_to_scope...")
        # 1. Initialize Memory
        memory = Memory(system_prompt="Dummy system prompt for explicit addition test.")

        # 2. Simulate a user message being pushed to memory
        domain_to_add = "specific-domain-to-test.com"
        user_message = f"Please add {domain_to_add} to our scope. Also check example.com."
        
        # Call push with role='user' and ensure auto_add_to_scope defaults to True
        memory.push(role='user', content=user_message)

        # 3. Inspect ScopeManager's domains list
        current_scope_domains = memory.scope.domains
        print(f"Domains in scope after explicit push: {current_scope_domains}")

        # 4. Assert that the domain IS present in the scope
        self.assertIn(domain_to_add, current_scope_domains,
                      f"FAILURE: Domain '{domain_to_add}' was NOT found in scope after explicit user message.")
        
        # Note: "example.com" is typically in the ScopeManager's exclude_patterns, so it should not be added.
        # We will assert it's NOT in scope.
        self.assertNotIn("example.com", current_scope_domains,
                         f"INFO: Domain 'example.com' was found in scope, but it is usually excluded. This might be unexpected depending on ScopeManager's exact exclude list.")

        # 5. Print success message
        if domain_to_add in current_scope_domains and "example.com" not in current_scope_domains:
            print(f"SUCCESS: Domain '{domain_to_add}' correctly added to scope, and 'example.com' (excluded) was not.")
        elif domain_to_add not in current_scope_domains:
            print(f"FAILURE: Domain '{domain_to_add}' was not added as expected.")
        else: # domain_to_add in scope but example.com also in scope
             print(f"PARTIAL SUCCESS/INFO: Domain '{domain_to_add}' added. 'example.com' was also added, check exclusion rules if this is not desired.")

        print(f"Final scope summary for explicit addition test:\n{memory.scope.get_scope_summary()}")


if __name__ == "__main__":
    # Create a dummy prompt file if it doesn't exist, to prevent FileNotFoundError
    try:
        with open("prompts/web_search_agent.txt", "r") as f:
            pass
    except FileNotFoundError:
        print("Creating dummy prompt file prompts/web_search_agent.txt")
        import os
        os.makedirs("prompts", exist_ok=True)
        with open("prompts/web_search_agent.txt", "w") as f:
            f.write("This is a dummy system prompt for the web search agent.")
            
    unittest.main()
