import asyncio
from agents.base_agent import Agent
from tools.file_finder import FileFinder
from tools.bash_executor import BashExecutor
from core.memory import Memory

class FileAgent(Agent):
    """
    Specialized agent for file operations and bash commands.
    Based on AgenticSeek's FileAgent with tool composition and retry logic.
    """
    
    def __init__(self, name, prompt_path, provider, work_dir, verbose=False):
        super().__init__(name, prompt_path, provider, verbose)
        
        self.work_dir = work_dir
        self.role = "files"
        self.type = "file_agent"
        
        # Import UI for better messaging
        try:
            from core.ui import ui
            self.ui = ui
        except ImportError:
            self.ui = None
        
        # Add specialized tools
        try:
            self.add_tool("file_finder", FileFinder())
            self.add_tool("bash", BashExecutor())
            if self.ui:
                self.ui.system_message(f"FileAgent tools initialized: file_finder, bash")
        except Exception as e:
            if self.ui:
                self.ui.status(f"FileAgent: Failed to add tools: {e}", "error")
            else:
                print(f"FileAgent: Failed to add tools: {e}")
        
        # Initialize memory with system prompt
        self.memory = Memory(self.system_prompt)
    
    async def process(self, prompt):
        """
        Process file-related requests with retry logic.
        Implements AgenticSeek's retry pattern with feedback loops.
        """
        exec_success = False
        
        # Add work directory and tool usage context
        enhanced_prompt = f"""{prompt}

You must work in directory: {self.work_dir}

For file operations, you can use:

1. **Bash commands** in ```bash blocks:
```bash
ls -la
find . -name "*.txt"
mkdir new_directory
cat file.txt
echo "content" > file.txt
```

2. **File finder operations** in ```file_finder blocks with format:
```file_finder
action=read
name=filename.txt
```

Available actions: info (default), read

Examples:
- To find and read a file: 
  ```file_finder
  action=read
  name=config.py
  ```
- To get file info:
  ```file_finder
  action=info
  name=document.pdf
  ```

Always explain what you're doing and provide clear feedback about results."""

        self.memory.push('user', enhanced_prompt)
        
        retry_count = 0
        max_retries = 3
        all_results = []  # Store all tool execution results
        
        # Main execution loop with retry logic
        while not exec_success and not self.stop and retry_count < max_retries:
            self.status_message = "Analyzing request..."
            if self.ui and retry_count > 0:
                self.ui.thinking(f"Retry attempt {retry_count}")
            
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
                # Add feedback to memory for retry - this is key to AgenticSeek's approach
                retry_feedback = f"The previous command failed: {feedback}. Please try a different approach."
                self.memory.push('user', retry_feedback)
                retry_count += 1
                if self.ui:
                    self.ui.status(f"Operation failed, retrying... ({retry_count}/{max_retries})", "warning")
            else:
                # Build final answer with actual results
                if all_results:
                    # Combine the LLM explanation with actual tool results
                    base_answer = self.remove_blocks(clean_answer)
                    self.last_answer = f"{base_answer}\n\nResults:\n" + "\n".join(all_results)
                else:
                    self.last_answer = self.remove_blocks(clean_answer)
        
        if retry_count >= max_retries:
            error_msg = "Operation failed after multiple attempts. Please try a different approach."
            if self.ui:
                self.ui.status("Max retries reached", "error")
            self.last_answer = error_msg
        
        self.status_message = "Ready"
        return self.last_answer