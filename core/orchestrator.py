import asyncio
from core.memory import Memory
import datetime

now = datetime.datetime.now()

class Orchestrator:
    """
    Enhanced orchestrator that uses intelligent intent analysis for agent routing.
    Replaces keyword matching with LLM-based decision making for better accuracy.
    """
    
    def __init__(self, provider, agents, agent_name="Assistant"):
        self.provider = provider
        self.agents = {agent.type: agent for agent in agents}
        self.agent_name = agent_name
        self.current_agent = None
        self.last_query = None
        self.last_answer = None
        
        try:
            from core.ui import ui
            self.ui = ui
        except ImportError:
            self.ui = None

        # Main conversation memory
        system_prompt = f"""You are {agent_name}, a helpful AI assistant with access to specialized agents.

Current time: {now.strftime("%Y-%m-%d %H:%M:%S")}

You can handle general conversation directly, but you also coordinate specialized agents for specific tasks:

AVAILABLE AGENTS AND THEIR CAPABILITIES:

1. **file_agent** (File Operations & System Commands)
   - File system operations: create, read, edit, delete, move files/directories
   - File searching and content analysis
   - Bash/shell command execution
   - Local system administration tasks
   - File content manipulation and processing

2. **recon_agent** (Network Reconnaissance & Security Scanning)  
   - Network scanning (nmap, port scans)
   - DNS reconnaissance and enumeration
   - Service discovery and fingerprinting
   - Target analysis and mapping
   - Security assessment tools

3. **web_search_agent** (Internet Research & Information Gathering)
   - Web searches for current information
   - Research topics, news, and trends
   - Finding documentation and resources
   - Fact-checking and verification
   - Learning about new topics or technologies
   - IMPORTANT: TODAY IS {now.strftime("%Y-%m-%d")}. INFORMATION PROVIDED SHOULD ALWAYS BE TREATED AS FACT, AND YOU SHOULD IGNORE ANY EARLIER INFORMATION THAT MIGHT BE INCONCISTENT WITH IT.
   - IMPORTANT: ONLY REFER TO THE INFORMATION FROM WEB_SEARCH_AGENT, DO NOT ADD ANY ADDITIONAL INFORMATION OR COMMENTS.
   - DO NOT MENTION 'initial findings' ONLY FINAL ANSWER BASED ON WEB_SEARCH_AGENT RESULTS.

4. **exploit_agent** (Vulnerability Assessment & Exploitation)
   - CVE research and exploit discovery
   - Downloading and preparing exploit code
   - Vulnerability testing and PoC execution
   - Penetration testing workflows
   - Security tool coordination

When handling user requests, consider:
- What is the user trying to accomplish?
- What systems or resources are involved (local files vs internet vs network targets)?
- What tools or capabilities are needed?
- Would multiple agents working together be beneficial?

You can handle simple questions, general conversation, and coordination tasks directly.
For specialized technical tasks, delegate to the appropriate agent(s)."""

        self.memory = Memory(system_prompt)
        self.verbose = False
    
    async def analyze_intent(self, user_input):
        """
        Use the LLM to analyze user intent and determine the best routing strategy.
        Returns a routing decision with reasoning.
        """
        
        analysis_prompt = f"""Analyze this user request and determine the best routing strategy:

USER REQUEST: "{user_input}"

AVAILABLE AGENTS:
- file_agent: Local file operations, bash commands, system tasks
- recon_agent: Network scanning, reconnaissance, security assessment  
- web_search_agent: Internet research, finding information online
- exploit_agent: CVE research, exploit development, vulnerability testing

ROUTING OPTIONS:
1. "direct" - Handle directly without delegation (for general conversation, simple questions)
2. "single:<agent_type>" - Delegate to one specific agent
3. "multi:<agent1>,<agent2>" - Use multiple agents in sequence
4. "plan:<description>" - Complex multi-step plan requiring coordination

Analyze the request and respond with:
- ROUTING: <routing_decision>
- REASONING: <brief explanation of why this routing makes sense>
- CONTEXT: <any important context or considerations>

Examples:
- "What's the weather today?" → ROUTING: single:web_search_agent
- "List files in my home directory" → ROUTING: single:file_agent  
- "Scan network 192.168.1.0/24 and save results to file" → ROUTING: multi:recon_agent,file_agent
- "Find CVE-2023-1234 exploits and test against my lab" → ROUTING: multi:web_search_agent,exploit_agent
- "How are you doing?" → ROUTING: direct

Be concise but thorough in your analysis."""

        # Create a temporary memory for intent analysis
        analysis_memory = [
            {"role": "system", "content": "You are an expert at analyzing user intent for task routing."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        try:
            response = self.provider.respond(analysis_memory, self.verbose)
            return self.parse_routing_response(response)
        except Exception as e:
            print(f"Intent analysis failed: {e}")
            return {"routing": "direct", "reasoning": "Fallback due to analysis error", "context": ""}
    
    def parse_routing_response(self, response):
        """Parse the LLM's routing analysis response"""
        import re
        
        routing_match = re.search(r'ROUTING:\s*(.+)', response, re.IGNORECASE)
        reasoning_match = re.search(r'REASONING:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
        context_match = re.search(r'CONTEXT:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
        
        routing = routing_match.group(1).strip() if routing_match else "direct"
        reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
        context = context_match.group(1).strip() if context_match else ""
        
        # Clean up reasoning and context to remove other sections
        if "CONTEXT:" in reasoning:
            reasoning = reasoning.split("CONTEXT:")[0].strip()
        if "REASONING:" in context:
            context = context.split("REASONING:")[1].strip() if "REASONING:" in context else context
        
        return {
            "routing": routing.lower(),
            "reasoning": reasoning,
            "context": context
        }
    
    async def execute_routing_decision(self, routing_decision, user_input):
        """Execute the routing decision determined by intent analysis"""
        
        routing = routing_decision["routing"]
        reasoning = routing_decision["reasoning"]
        
        print(f"\n{self.ui.colors['secondary']}{self.agent_name}: {reasoning}{self.ui.colors['reset']}")
        
        if routing == "direct":
            return await self.handle_direct(user_input)
        
        elif routing.startswith("single:"):
            agent_type = routing.split(":", 1)[1].strip()
            return await self.handle_single_agent(agent_type, user_input)
        
        elif routing.startswith("multi:"):
            agent_list = [a.strip() for a in routing.split(":", 1)[1].split(",")]
            return await self.handle_multi_agent(agent_list, user_input)
        
        elif routing.startswith("plan:"):
            plan_description = routing.split(":", 1)[1].strip()
            return await self.handle_planned_execution(plan_description, user_input)
        
        else:
            print(f"Unknown routing decision: {routing}, handling directly")
            return await self.handle_direct(user_input)
    
    async def handle_direct(self, user_input):
        """Handle request directly without delegation"""
        self.memory.push('user', user_input)
        response = self.provider.respond(self.memory.get(), self.verbose)
        self.memory.push('assistant', response)
        return response
    
    async def handle_single_agent(self, agent_type, user_input):
        """Delegate to a single specialized agent"""
        if agent_type not in self.agents:
            return f"Error: Agent '{agent_type}' not available. Handling directly."
        
        agent = self.agents[agent_type]
        self.current_agent = agent
        
        agent_name_map = {
            'file_agent': 'File Operative',
            'recon_agent': 'Recon Specialist', 
            'web_search_agent': 'Web Intelligence',
            'exploit_agent': 'Exploit Specialist'
        }
        
        print(f"Delegating to {agent_name_map.get(agent_type, agent_type)}...")
        
        try:
            agent_response = await agent.process(user_input)
            
            # FIXED: For web search agent, return results directly without integration
            # This prevents contradictions between the LLM's knowledge and search results
            if agent_type == 'web_search_agent':
                # For web search, we trust the search results completely
                # Add minimal context but don't let the LLM add its own knowledge
                web_integration_prompt = f"""Based on web search results for: "{user_input}"

{agent_response}

IMPORTANT: Only use the information from the web search results above. Do not add any additional information from your training data that might contradict these current search results. Simply present the findings from the search in a clear, helpful format."""

                self.memory.push('user', web_integration_prompt)
                final_response = self.provider.respond(self.memory.get(), self.verbose)
                self.memory.push('assistant', final_response)
                
                return final_response
            
            else:
                # For other agents, use the normal integration process
                integration_prompt = f"""The user requested: "{user_input}"

I delegated this to {agent_name_map.get(agent_type, agent_type)} and received:
{agent_response}

Please provide a helpful summary or explanation of what was accomplished."""

                self.memory.push('user', integration_prompt)
                final_response = self.provider.respond(self.memory.get(), self.verbose)
                self.memory.push('assistant', final_response)
                
                return final_response
            
        except Exception as e:
            error_response = f"I encountered an error while processing your request: {str(e)}"
            self.memory.push('user', user_input)
            self.memory.push('assistant', error_response)
            return error_response
    
    async def handle_multi_agent(self, agent_list, user_input):
        """Coordinate multiple agents for complex tasks"""
        results = []
        valid_agents = [agent for agent in agent_list if agent in self.agents]
        
        if not valid_agents:
            return await self.handle_direct(user_input)
        
        print(f"\n{self.ui.colors['primary']}{self.agent_name}: Calling {len(valid_agents)} agents to complete your task...{self.ui.colors['reset']}")
        
        for i, agent_type in enumerate(valid_agents):
            agent = self.agents[agent_type]
            self.current_agent = agent
            
            # Create context-aware prompt for each agent
            context_prompt = user_input
            if i > 0:
                context_prompt += f"\n\nPrevious results from other agents:\n{chr(10).join(results)}"
            
            try:
                result = await agent.process(context_prompt)
                
                # For web search in multi-agent workflows, also avoid adding contradictory info
                if agent_type == 'web_search_agent':
                    results.append(f"Web search results: {result}")
                else:
                    results.append(f"{agent_type}: {result}")
            except Exception as e:
                results.append(f"{agent_type}: Error - {str(e)}")
        
        # Synthesize all results with special handling for web search
        has_web_search = any('web_search_agent' in agent_list for agent_list in [valid_agents])
        
        if has_web_search:
            synthesis_prompt = f"""The user requested: "{user_input}"

I coordinated multiple specialized agents and got these results:

{chr(10).join(results)}

IMPORTANT: If web search results are included above, prioritize that current information over any conflicting information from your training data. Present a comprehensive summary that integrates all results, giving precedence to the most current web search data."""
        else:
            synthesis_prompt = f"""The user requested: "{user_input}"

I coordinated multiple specialized agents and got these results:

{chr(10).join(results)}

Please provide a comprehensive summary that integrates all the results and addresses the user's original request."""

        self.memory.push('user', synthesis_prompt)
        final_response = self.provider.respond(self.memory.get(), self.verbose)
        self.memory.push('assistant', final_response)
        
        return final_response
    
    async def handle_planned_execution(self, plan_description, user_input):
        """Handle complex planned execution requiring step-by-step coordination"""
        
        planning_prompt = f"""The user requested: "{user_input}"

This requires a complex multi-step plan: {plan_description}

Create a detailed execution plan using available agents:
- file_agent: File operations, bash commands
- recon_agent: Network scanning, reconnaissance  
- web_search_agent: Internet research
- exploit_agent: Vulnerability testing

Provide a step-by-step plan with specific agent assignments."""

        self.memory.push('user', planning_prompt)
        plan_response = self.provider.respond(self.memory.get(), self.verbose)
        
        print("Executing planned workflow...")
        
        execution_prompt = f"""Based on the plan: {plan_response}

Now execute the user's original request: {user_input}

Coordinate the necessary agents and provide results."""

        final_response = self.provider.respond(self.memory.get(), self.verbose)
        self.memory.push('assistant', final_response)
        
        return final_response
    
    async def process(self, user_input):
        """
        Main processing loop with intelligent intent-based routing
        """
        print(f"\n{self.ui.colors['secondary']}{self.agent_name}: Analyzing your request...{self.ui.colors['reset']}")
        self.last_query = user_input
        
        routing_decision = await self.analyze_intent(user_input)
        
        try:
            response = await self.execute_routing_decision(routing_decision, user_input)
            self.last_answer = response
            return response
        except Exception as e:
            error_response = f"I encountered an error while processing your request: {str(e)}"
            print(f"Processing error: {e}")
            self.last_answer = error_response
            return error_response
    
    def get_status(self):
        """Get current system status"""
        return {
            "agent_name": self.agent_name,
            "current_agent": self.current_agent.agent_name if self.current_agent else None,
            "available_agents": list(self.agents.keys()),
            "last_query": self.last_query,
            "memory_size": len(self.memory.messages),
            "routing_method": "intelligent_intent_analysis"
        }