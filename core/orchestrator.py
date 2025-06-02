import asyncio
from core.memory import Memory

class Orchestrator:
    def __init__(self, provider, agents, agent_name="Assistant"):
        self.provider = provider
        self.agents = {agent.type: agent for agent in agents}
        self.agent_name = agent_name
        self.current_agent = None
        self.last_query = None
        self.last_answer = None
        
        system_prompt = f"""You are {agent_name}, a penetration testing AI assistant with specialized agents.

AVAILABLE SPECIALIZED AGENTS:

FILE AGENT - File operations and management
Use for: listing files, reading files, creating directories, file navigation, viewing file contents

FILE EXECUTOR - Script and code execution  
Use for: running scripts, executing code, bash commands, python scripts, any file execution

RECON AGENT - Network reconnaissance and scanning
Use for: nmap scans, port scanning, service enumeration, network discovery

WEB SEARCH AGENT - Online research and information gathering
Use for: searching for CVE information, researching vulnerabilities, finding documentation

EXPLOIT AGENT - Exploit discovery, download, and preparation
Use for: downloading exploits, finding CVE exploits, preparing payloads

DELEGATION GUIDELINES:
- If user wants to RUN, EXECUTE, or use BASH on files → File Executor
- If user wants to LIST, READ, or VIEW files → File Agent  
- If user wants to SCAN or do reconnaissance → Recon Agent
- If user wants to SEARCH for information → Web Search Agent
- If user wants to DOWNLOAD or find exploits → Exploit Agent

SCOPE COMMANDS (handle directly):
- "show scope" / "scope" - Display current targets
- "clear scope" - Remove all targets
- "add <target> to scope" - Add IP/domain/network  
- "remove <target> from scope" - Remove target

Always show actual results and provide clear, specific responses."""

        self.memory = Memory(system_prompt)
        self.verbose = False
    
    def handle_scope_command(self, user_input: str) -> str:
        input_lower = user_input.lower().strip()
        
        file_operation_indicators = ['list', 'file', 'directory', 'folder', 'ls', 'bash', 'run', 'execute', 'cat', 'head', 'tail', '.txt', '.pdf', '.sh', '.py', '.log']
        if any(indicator in input_lower for indicator in file_operation_indicators):
            return None
        
        if input_lower in ['show scope', 'scope', 'list scope', 'current scope']:
            return self.memory.scope.get_scope_summary()
        
        if input_lower in ['clear scope', 'reset scope']:
            if self.memory.scope.is_empty():
                return "Scope is already empty."
            self.memory.scope.clear_scope()
            return "Scope cleared. All targets removed."
        
        if 'add' in input_lower and 'scope' in input_lower:
            import re
            ip_match = re.search(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', user_input)
            domain_match = re.search(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:com|org|net|edu|gov|mil|io|co|uk|ca|de|fr|jp|au|in|cn|ru|br)\b', user_input)
            network_match = re.search(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/(?:[0-9]|[1-2][0-9]|3[0-2])\b', user_input)
            
            if any(word in input_lower for word in ['list', 'file', 'directory', 'folder', 'ls', 'bash', 'run', 'execute', 'cat', 'head', 'tail', '.txt', '.pdf', '.sh', '.py']):
                return None
            
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
        
        if 'remove' in input_lower and 'scope' in input_lower:
            import re
            ip_match = re.search(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', user_input)
            domain_match = re.search(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:com|org|net|edu|gov|mil|io|co|uk|ca|de|fr|jp|au|in|cn|ru|br)\b', user_input)
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
        
        return None
    
    def should_delegate_to_agent(self, prompt):
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['run', 'execute', 'bash', 'python', 'script']):
            return 'file_executor_agent'
        
        if any(word in prompt_lower for word in ['exploit', 'cve', 'download', 'payload', 'vulnerability']):
            if not any(word in prompt_lower for word in ['list', 'show', 'read']):
                return 'exploit_agent'
        
        if any(word in prompt_lower for word in ['scan', 'nmap', 'recon', 'enumerate', 'port']):
            return 'recon_agent'
        
        if any(word in prompt_lower for word in ['list', 'show', 'read', 'cat', 'head', 'tail', 'view']):
            if any(word in prompt_lower for word in ['file', 'directory', 'folder']):
                return 'file_agent'
        
        if any(word in prompt_lower for word in ['search', 'research', 'find information', 'look up']):
            return 'web_search_agent'
        
        return None
    
    async def process(self, user_input):
        print(f"\n{self.agent_name}: Processing your request...")
        self.last_query = user_input
        
        scope_response = self.handle_scope_command(user_input)
        if scope_response:
            self.memory.push('user', user_input)
            self.memory.push('assistant', scope_response)
            self.last_answer = scope_response
            return scope_response
        
        agent_type = self.should_delegate_to_agent(user_input)
        
        if agent_type and agent_type in self.agents:
            agent_name_map = {
                'file_agent': 'File Operative',
                'file_executor_agent': 'File Executor',
                'recon_agent': 'Recon Specialist',
                'web_search_agent': 'Research Agent',
                'exploit_agent': 'Exploit Specialist'
            }
            print(f"Delegating to {agent_name_map.get(agent_type, agent_type)}...")
            
            agent = self.agents[agent_type]
            self.current_agent = agent
            
            try:
                enhanced_user_input = user_input
                if not self.memory.scope.is_empty():
                    scope_context = f"\n\nCurrent scope: {self.memory.scope.get_scope_summary()}\nFocus operations on scoped targets only."
                    enhanced_user_input += scope_context
                
                agent_response = await agent.process(enhanced_user_input)
                
                if agent_type == 'file_executor_agent':
                    integration_prompt = f"""User requested: "{user_input}"

File Executor response:
{agent_response}

Show the user exactly what happened when the script was executed. Include any output, errors, or results from running the code."""

                elif agent_type == 'file_agent':
                    integration_prompt = f"""User requested: "{user_input}"

File Agent response:
{agent_response}

Show the user the actual file operation results - file listings, file contents, or directory information as requested."""

                elif agent_type == 'recon_agent':
                    integration_prompt = f"""User requested: "{user_input}"

Recon Agent response:
{agent_response}

Show the user the actual reconnaissance results - scan outputs, discovered services, open ports, or enumeration findings."""

                elif agent_type == 'exploit_agent':
                    integration_prompt = f"""User requested: "{user_input}"

Exploit Agent response:
{agent_response}

Show the user what exploit operations were completed - downloaded files, prepared payloads, or execution results."""

                elif agent_type == 'web_search_agent':
                    integration_prompt = f"""User requested: "{user_input}"

Research Agent response:
{agent_response}

Show the user the research findings and information discovered."""

                else:
                    integration_prompt = f"""User requested: "{user_input}"

Agent response: {agent_response}

Provide a clear summary of what was accomplished."""

                self.memory.push('user', integration_prompt)
                final_response = self.provider.respond(self.memory.get(), self.verbose)
                self.memory.push('assistant', final_response)
                
                self.last_answer = final_response
                return final_response
                
            except Exception as e:
                error_response = f"Error processing request: {str(e)}"
                self.memory.push('user', user_input)
                self.memory.push('assistant', error_response)
                self.last_answer = error_response
                return error_response
        else:
            self.memory.push('user', user_input)
            response = self.provider.respond(self.memory.get(), self.verbose)
            self.memory.push('assistant', response)
            
            self.last_answer = response
            return response
    
    def get_status(self):
        base_status = {
            "agent_name": self.agent_name,
            "current_agent": self.current_agent.agent_name if self.current_agent else None,
            "available_agents": list(self.agents.keys()),
            "last_query": self.last_query,
            "memory_size": len(self.memory.messages)
        }
        
        base_status["scope_targets"] = len(self.memory.scope.get_all_targets())
        base_status["scope_active"] = not self.memory.scope.is_empty()
        
        return base_status