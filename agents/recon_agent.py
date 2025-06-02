import asyncio
from agents.base_agent import Agent
from tools.bash_executor import BashExecutor
from core.memory import Memory

class ReconAgent(Agent):
    """
    Specialized agent for reconnaissance operations using bash commands.
    Based on AgenticSeek's agent patterns with focus on target reconnaissance.
    """
    
    def __init__(self, name, prompt_path, provider, work_dir, verbose=False):
        super().__init__(name, prompt_path, provider, verbose)
        
        self.work_dir = work_dir
        self.role = "reconnaissance"
        self.type = "recon_agent"
        
        # Import UI for better messaging
        try:
            from core.ui import ui
            self.ui = ui
        except ImportError:
            self.ui = None
        
        # Add bash execution tool for recon commands
        try:
            self.add_tool("bash", BashExecutor())
            if self.ui:
                self.ui.system_message(f"ReconAgent tools initialized: bash executor")
        except Exception as e:
            if self.ui:
                self.ui.status(f"ReconAgent: Failed to add tools: {e}", "error")
            else:
                print(f"ReconAgent: Failed to add tools: {e}")
        
        # Initialize memory with system prompt
        self.memory = Memory(self.system_prompt)
    
    async def process(self, prompt):
        """
        Process reconnaissance requests with retry logic.
        Implements AgenticSeek's retry pattern with safety considerations.
        """
        exec_success = False
        
        # Add work directory and recon context
        enhanced_prompt = f"""{prompt}

You must work in directory: {self.work_dir}

For reconnaissance operations, use bash commands in ```bash blocks:

Light scan:
```bash
nmap --min-rate=1000 -p 22,80,443,8080 -T4 target -oN light-scan.txt
```
Secondary Scan:
```bash
nmap -sC -sV --top-ports 1000 target -oN secondary-scan.txt
```

```bash
dig target
```

```bash
whois target
```

IMPORTANT SAFETY GUIDELINES:
1. Only scan targets you have explicit permission to test
2. Use reasonable rate limits to avoid overwhelming targets
3. Always save scan results to files for documentation
4. Be respectful of network resources
5. Follow responsible disclosure practices

Always explain what reconnaissance you're performing and why."""

        self.memory.push('user', enhanced_prompt)
        
        retry_count = 0
        max_retries = 3
        all_results = []  # Store all command execution results
        
        # Main execution loop with retry logic
        while not exec_success and not self.stop and retry_count < max_retries:
            self.status_message = "Planning reconnaissance..."
            if self.ui and retry_count > 0:
                self.ui.thinking(f"Recon retry attempt {retry_count}")
            
            # Get LLM response
            response = self.provider.respond(self.memory.get(), self.verbose)
            
            # Extract reasoning and clean answer
            self.last_reasoning = self.extract_reasoning_text(response)
            clean_answer = self.remove_reasoning_text(response)
            
            # Store response in memory
            self.memory.push('assistant', clean_answer)
            
            # Execute any tools found in the response
            exec_success, feedback = self.execute_modules(response)
            
            # Store tool results for final answer
            if exec_success and feedback and "[success]" in feedback:
                # Extract the actual tool output from feedback
                tool_output = feedback.split(":\n", 1)[1] if ":\n" in feedback else feedback
                all_results.append(tool_output)
            
            if not exec_success and feedback:
                # Add feedback to memory for retry
                retry_feedback = f"The previous reconnaissance command failed: {feedback}. Please try a different approach or check the target/command syntax."
                self.memory.push('user', retry_feedback)
                retry_count += 1
                if self.ui:
                    self.ui.status(f"Recon operation failed, retrying... ({retry_count}/{max_retries})", "warning")
            else:
                # Build final answer with actual results
                if all_results:
                    # Combine the LLM explanation with actual command results
                    base_answer = self.remove_blocks(clean_answer)
                    self.last_answer = f"{base_answer}\n\nReconnaissance Results:\n" + "\n".join(all_results)
                else:
                    self.last_answer = self.remove_blocks(clean_answer)
        
        if retry_count >= max_retries:
            error_msg = "Reconnaissance operation failed after multiple attempts. Please verify target accessibility and command syntax."
            if self.ui:
                self.ui.status("Max recon retries reached", "error")
            self.last_answer = error_msg
        
        self.status_message = "Ready"
        return self.last_answer