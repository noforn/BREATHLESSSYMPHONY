# Enhanced version of core/orchestrator.py
# This extends the existing orchestrator with scope management

import asyncio
from core.memory import Memory

class Orchestrator:
    """
    Enhanced orchestrator with scope management and pentest workflow support.
    Maintains backward compatibility while adding scope tracking.
    """
    
    def __init__(self, provider, agents, agent_name="Assistant"):
        self.provider = provider
        self.agents = {agent.type: agent for agent in agents}
        self.agent_name = agent_name
        self.current_agent = None
        self.last_query = None
        self.last_answer = None
        
        # Enhanced system prompt with scope awareness
        system_prompt = f"""You are {agent_name}, a penetration testing AI assistant.

You can handle general conversation, but you also have access to specialized agents for specific tasks:
- file_agent: For file operations, searching files, running bash commands
- recon_agent: For reconnaissance operations, network scanning, target enumeration  
- web_search_agent: For web searches, finding information online, research

PENETRATION TESTING SCOPE MANAGEMENT:
You automatically track penetration test scope (IP addresses, domains, networks) mentioned in conversations.
Always consider the current scope when performing operations. Focus reconnaissance and testing efforts on targets within scope.

When a user requests something that requires specialized capabilities, you should:
1. Determine if you need a specialized agent
2. If yes, delegate the task and integrate the results
3. If no, handle it yourself

SCOPE COMMANDS (handle these directly without delegation):
- "show scope" / "scope" - Display current targets
- "clear scope" - Remove all targets from scope  
- "add <target> to scope" - Manually add IP/domain/network
- "remove <target> from scope" - Remove specific target

Always be helpful and provide clear, useful responses."""

        self.memory = Memory(system_prompt)
        self.verbose = False
    
    def handle_scope_command(self, user_input: str) -> str:
        """Handle scope management commands directly"""
        input_lower = user_input.lower().strip()
        
        # Show scope command
        if input_lower in ['show scope', 'scope', 'list scope', 'current scope']:
            return self.memory.scope.get_scope_summary()
        
        # Clear scope command
        if input_lower in ['clear scope', 'reset scope']:
            if self.memory.scope.is_empty():
                return "Scope is already empty."
            self.memory.scope.clear_scope()
            return "Scope cleared. All targets removed."
        
        # Add to scope command
        if 'add' in input_lower and 'scope' in input_lower:
            # Extract target from "add <target> to scope"
            import re
            # Look for IP addresses
            ip_match = re.search(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', user_input)
            # Look for domains
            domain_match = re.search(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b', user_input)
            # Look for networks
            network_match = re.search(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/(?:[0-9]|[1-2][0-9]|3[0-2])\b', user_input)
            
            if network_match:
                target = network_match.group()
                if self.memory.scope.add_network(target):
                    return f"Added network {target} to scope."
                else:
                    return f"Failed to add {target} to scope (invalid network or already exists)."
            elif ip_match:
                target = ip_match.group()
                if self.memory.scope.add_target(target):
                    return f"Added IP {target} to scope."
                else:
                    return f"Failed to add {target} to scope (invalid IP or already exists)."
            elif domain_match:
                target = domain_match.group()
                if self.memory.scope.add_domain(target):
                    return f"Added domain {target} to scope."
                else:
                    return f"Failed to add {target} to scope (already exists)."
            else:
                return "No valid target found. Please specify an IP address, domain, or network (e.g., 'add 192.168.1.1 to scope')."
        
        # Remove from scope command
        if 'remove' in input_lower and 'scope' in input_lower:
            import re
            # Look for any target type
            ip_match = re.search(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', user_input)
            domain_match = re.search(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b', user_input)
            network_match = re.search(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/(?:[0-9]|[1-2][0-9]|3[0-2])\b', user_input)
            
            target = None
            if network_match:
                target = network_match.group()
            elif ip_match:
                target = ip_match.group()
            elif domain_match:
                target = domain_match.group()
            
            if target:
                if self.memory.scope.remove_target(target):
                    return f"Removed {target} from scope."
                else:
                    return f"{target} was not in scope."
            else:
                return "No valid target found to remove. Please specify an IP address, domain, or network."
        
        return None  # Not a scope command
    
    def should_delegate_to_agent(self, prompt):
        """
        Enhanced delegation logic with scope awareness.
        Same as original but now considers scope context.
        """
        file_keywords = [
            'file', 'directory', 'folder', 'bash', 'command', 'list', 
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
            'search', 'google', 'web', 'online', 'lookup',
            'research', 'find information', 'look up', 'search for', 'ddg',
            'news', 'latest', 'current', 'recent', 'today', 'yesterday', 
            'this week', 'this month', 'updates', 'trends',
            'who is', 'how to', 'when did', 'what are', 'who are', 'how do', 'when was',
            'information about', 'details about', 'facts about', 'data on',
            'statistics', 'reports', 'articles', 'studies', 'reviews',
            'learn about', 'understand', 'tutorial', 'guide', 'exploit', 'cve', 'vulnerability'
        ]
        
        prompt_lower = prompt.lower()
        
        # Check for web search operations first (most common)
        if any(keyword in prompt_lower for keyword in web_search_keywords):
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
        Enhanced processing with scope command handling.
        """
        print(f"\n{self.agent_name}: Processing your request...")
        self.last_query = user_input
        
        # NEW: Handle scope commands directly
        scope_response = self.handle_scope_command(user_input)
        if scope_response:
            self.memory.push('user', user_input)
            self.memory.push('assistant', scope_response)
            self.last_answer = scope_response
            return scope_response
        
        # Check if we need to delegate to a specialized agent
        agent_type = self.should_delegate_to_agent(user_input)
        
        if agent_type and agent_type in self.agents:
            # Delegate to specialized agent with scope context
            agent_name_map = {
                'file_agent': 'File Operative',
                'recon_agent': 'Recon Specialist',
                'web_search_agent': 'Research Agent'
            }
            print(f"Delegating to {agent_name_map.get(agent_type, agent_type)}...")
            
            agent = self.agents[agent_type]
            self.current_agent = agent
            
            try:
                # Enhanced prompt with scope context for agents
                enhanced_user_input = user_input
                if not self.memory.scope.is_empty():
                    scope_context = f"\n\nREMINDER - Current penetration test scope:\n{self.memory.scope.get_scope_summary()}\n\nFocus your operations on the targets within scope."
                    enhanced_user_input += scope_context
                
                agent_response = await agent.process(enhanced_user_input)
                
                # Integration logic (same as original)
                if agent_type == 'web_search_agent':
                    integration_prompt = f"""The user asked: "{user_input}"

I delegated this to a web search specialist and received current, up-to-date information:
{agent_response}

IMPORTANT: The web search results above contain CURRENT information that is more recent and accurate than my training data. I should present these findings as the authoritative answer and NOT contradict them with older information from my training. If the web search results differ from what I might have known previously, the web search results are correct. ALWAYS present the web search results as the final answer.

Please summarize these current findings clearly and accurately."""
                else:
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
        """Enhanced status with scope information"""
        base_status = {
            "agent_name": self.agent_name,
            "current_agent": self.current_agent.agent_name if self.current_agent else None,
            "available_agents": list(self.agents.keys()),
            "last_query": self.last_query,
            "memory_size": len(self.memory.messages)
        }
        
        # NEW: Add scope status
        base_status["scope_targets"] = len(self.memory.scope.get_all_targets())
        base_status["scope_active"] = not self.memory.scope.is_empty()
        
        return base_status