import asyncio
from core.memory import Memory
import datetime

now = datetime.datetime.now()

class Orchestrator:
    """
    Main orchestrator that handles conversation flow and agent routing.
    Enhanced with comprehensive web search routing.
    """
    
    def __init__(self, provider, agents, agent_name="Assistant"):
        self.provider = provider
        self.agents = {agent.type: agent for agent in agents}
        self.agent_name = agent_name
        self.current_agent = None
        self.last_query = None
        self.last_answer = None
        
        # Main conversation memory
        system_prompt = f"""You are {agent_name}, a helpful AI assistant. 

Current time: {now.strftime("%Y-%m-%d %H:%M:%S")}

You can handle general conversation, but you also have access to specialized agents for specific tasks:
- file_agent: For file operations, searching files, running bash commands
- recon_agent: For reconnaissance operations, network scanning, target enumeration  
- web_search_agent: For web searches, finding information online, research

When a user requests something that requires specialized capabilities, you should:
1. Determine if you need a specialized agent
2. If yes, delegate the task and integrate the results
3. If no, handle it yourself

Always be helpful and provide clear, useful responses."""

        self.memory = Memory(system_prompt)
        self.verbose = False
    
    def should_delegate_to_agent(self, prompt):
        """
        Determine if prompt needs a specialized agent.
        Enhanced web search detection.
        """
        file_keywords = [
            'file', 'directory', 'folder', 'bash', 'command', 'find', 
            'ls', 'cd', 'mkdir', 'rm', 'create', 'delete', 'move', 'copy', 
            'read', 'write', 'save', 'download', 'upload'
        ]
        
        recon_keywords = [
            'recon', 'reconnaissance', 'scan', 'nmap', 'port', 'target', 
            'enumerate', 'enumeration', 'dig', 'dns', 'whois', 'network',
            'ping', 'traceroute', 'subdomain', 'service', 'vulnerability',
            'footprint', 'fingerprint', 'discovery', 'mapping', 'probe'
        ]
        
        web_search_keywords = [
            # Direct search terms
            'search', 'google', 'web', 'internet', 'online', 'lookup',
            'research', 'find information', 'look up', 'search for',
            
            # Information seeking
            'news', 'latest', 'current', 'recent', 'today', 'yesterday', 
            'this week', 'this month', 'updates', 'trends',
            
            # Question patterns
            'what is', 'who is', 'how to', 'when did', 'where is',
            'what are', 'who are', 'how do', 'when was', 'where are',
            
            # Information types
            'information about', 'details about', 'facts about', 'data on',
            'statistics', 'reports', 'articles', 'studies', 'reviews',
            
            # Learning and help
            'learn about', 'understand', 'explain', 'tutorial', 'guide',
            'help with', 'show me', 'tell me about'
        ]
        
        prompt_lower = prompt.lower()
        
        # Check for web search operations first (most common)
        if any(keyword in prompt_lower for keyword in web_search_keywords):
            # Make sure it's not a file search or recon operation
            if not any(keyword in prompt_lower for keyword in file_keywords + recon_keywords):
                return 'web_search_agent'
        
        # Check for reconnaissance operations (more specific)
        if any(keyword in prompt_lower for keyword in recon_keywords):
            return 'recon_agent'
        
        # Check for file-related operations  
        if any(keyword in prompt_lower for keyword in file_keywords):
            return 'file_agent'
        
        return None
    
    async def process(self, user_input):
        """
        Main processing loop that routes between agents.
        """
        print(f"\n{self.agent_name}: Processing your request...")
        self.last_query = user_input
        
        # Check if we need to delegate to a specialized agent
        agent_type = self.should_delegate_to_agent(user_input)
        
        if agent_type and agent_type in self.agents:
            # Delegate to specialized agent
            agent_name_map = {
                'file_agent': 'File Operative',
                'recon_agent': 'Recon Specialist',
                'web_search_agent': 'Web Intelligence'
            }
            print(f"Delegating to {agent_name_map.get(agent_type, agent_type)}...")
            
            agent = self.agents[agent_type]
            self.current_agent = agent
            
            try:
                agent_response = await agent.process(user_input)
                
                # Integrate the agent's response into our conversation
                if agent_type == 'web_search_agent':
                    # For web search results, prioritize fresh data over training knowledge
                    integration_prompt = f"""The user asked: "{user_input}"

I delegated this to a web search specialist and received current, up-to-date information:
{agent_response}

IMPORTANT: The web search results above contain CURRENT information that is more recent and accurate than my training data. I should present these findings as the authoritative answer and NOT contradict them with older information from my training. If the web search results differ from what I might have known previously, the web search results are correct.

Please summarize these current findings clearly and accurately."""
                else:
                    # For other agents, use standard integration
                    integration_prompt = f"""The user asked: "{user_input}"

I delegated this to a specialized agent and got this response:
{agent_response}

Please provide a helpful summary or explanation of what was accomplished."""

                self.memory.push('user', integration_prompt)
                final_response = self.provider.respond(self.memory.get(), self.verbose)
                self.memory.push('assistant', final_response)
                
                self.last_answer = final_response
                return final_response
                
            except Exception as e:
                error_response = f"I encountered an error while processing your request: {str(e)}"
                self.memory.push('user', user_input)
                self.memory.push('assistant', error_response)
                self.last_answer = error_response
                return error_response
        else:
            # Handle directly with main conversation agent
            self.memory.push('user', user_input)
            response = self.provider.respond(self.memory.get(), self.verbose)
            self.memory.push('assistant', response)
            
            self.last_answer = response
            return response
    
    def get_status(self):
        """Get current system status"""
        return {
            "agent_name": self.agent_name,
            "current_agent": self.current_agent.agent_name if self.current_agent else None,
            "available_agents": list(self.agents.keys()),
            "last_query": self.last_query,
            "memory_size": len(self.memory.messages)
        }
