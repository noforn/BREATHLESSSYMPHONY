from abc import abstractmethod
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

class Agent:
    """
    Abstract base class for all agents.
    Based on AgenticSeek's Agent class with core functionality.
    """
    
    def __init__(self, name, prompt_path, provider, verbose=False):
        self.agent_name = name
        self.provider = provider
        self.verbose = verbose
        self.tools = {}
        self.success = True
        self.last_answer = ""
        self.last_reasoning = ""
        self.status_message = "Ready"
        self.stop = False
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # Import UI for better output formatting
        try:
            from core.ui import ui
            self.ui = ui
        except ImportError:
            self.ui = None
        
        # Load system prompt
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            self.system_prompt = f"You are {name}, a helpful AI assistant."
    
    def add_tool(self, name, tool):
        """Add a tool to this agent"""
        self.tools[name] = tool
    
    def extract_reasoning_text(self, text):
        """Extract <think>...</think> blocks from reasoning models like DeepSeek"""
        if text is None:
            return None
        
        start_tag = "<think>"
        end_tag = "</think>"
        start_idx = text.find(start_tag)
        end_idx = text.rfind(end_tag)
        
        if start_idx != -1 and end_idx != -1:
            return text[start_idx:end_idx + len(end_tag)]
        return None
    
    def remove_reasoning_text(self, text):
        """Remove <think>...</think> blocks from output"""
        if text is None:
            return text
            
        pattern = r'<think>.*?</think>'
        return re.sub(pattern, '', text, flags=re.DOTALL).strip()
    
    def remove_blocks(self, text):
        """Replace code blocks with placeholders like block:0"""
        pattern = r'```.*?\n.*?\n```'
        block_idx = 0
        
        def replace_block(match):
            nonlocal block_idx
            result = f"block:{block_idx}"
            block_idx += 1
            return result
        
        return re.sub(pattern, replace_block, text, flags=re.DOTALL)
    
    def execute_modules(self, answer):
        """
        Execute all tools on the answer and return success status.
        This is the core of AgenticSeek's block execution system.
        OPTIMIZED: Only process tools that have blocks, avoid redundant checks.
        """
        success = True
        feedback = ""
        executed_tools = 0
        
        self.success = True
        
        for name, tool in self.tools.items():
            # Load executable blocks from the answer
            blocks, save_path = tool.load_exec_block(answer)
            
            # OPTIMIZATION: Skip tools with no blocks
            if blocks is None or len(blocks) == 0:
                continue
                
            executed_tools += 1
            
            # Use UI for better tool execution display
            if self.ui:
                self.ui.tool_execution(name, len(blocks))
            else:
                print(f"Executing {len(blocks)} {name} blocks...")
            
            # Execute the blocks
            output = tool.execute(blocks)
            feedback = tool.interpreter_feedback(output)
            
            # OPTIMIZATION: execution_failure_check called only once here
            tool_success = not tool.execution_failure_check(output)
            
            if not tool_success:
                self.success = False
                success = False
                break
            
            # Save blocks to file if specified
            if save_path is not None:
                tool.save_block(blocks, save_path)
        
        if executed_tools == 0:
            if self.ui:
                self.ui.system_message("No executable blocks found in response")
            else:
                print("No executable blocks found in response")
        
        return success, feedback
    
    async def llm_request(self):
        """
        Asynchronously ask the LLM to process the prompt.
        Uses ThreadPoolExecutor to avoid blocking the event loop.
        """
        self.status_message = "Thinking..."
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.sync_llm_request)
    
    def sync_llm_request(self):
        """Synchronous LLM request"""
        memory = self.memory.get()
        thought = self.provider.respond(memory, self.verbose)

        reasoning = self.extract_reasoning_text(thought)
        answer = self.remove_reasoning_text(thought)
        self.memory.push('assistant', answer)
        return answer, reasoning
    
    def request_stop(self):
        """Request the agent to stop processing"""
        self.stop = True
        self.status_message = "Stopped"
    
    @abstractmethod
    async def process(self, prompt):
        """Process a prompt and return response - must be implemented by subclasses"""
        pass