import subprocess
import os
import re
from tools.tools import Tools

class BashExecutor(Tools):
    """
    Tool for executing bash/shell commands safely.
    """
    def __init__(self):
        super().__init__()
        self.tag = "bash"
        self.name = "Bash Executor"
        self.description = "Executes bash/shell commands safely in the working directory"
    
    def execute(self, blocks: list, safety: bool = False) -> str:
        """Execute bash commands safely"""
        if not blocks:
            return "Error: No commands provided"
        output = ""
        for i, block in enumerate(blocks):
            command = f"cd {self.work_dir} && {block.strip()}"
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.work_dir,
                    timeout=30
                )
                if result.stdout:
                    output += result.stdout
                if result.stderr:
                    error_msg = f"\nError: {result.stderr}"
                    output += error_msg
                if not result.stdout and not result.stderr:
                    if result.returncode == 0:
                        success_msg = "Command executed successfully"
                        output += success_msg
                    else:
                        error_msg = f"Command failed with return code {result.returncode}"
                        output += error_msg
            except subprocess.TimeoutExpired:
                timeout_msg = "Error: Command timed out after 30 seconds"
                output += timeout_msg
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                output += error_msg
        final_output = output.strip()
        return final_output
    
    def execution_failure_check(self, output: str) -> bool:
        """Check if execution had errors using pattern matching"""
        error_patterns = [
            r"error", r"failed", r"invalid", r"exception", 
            r"not found", r"denied", r"timeout", r"permission",
            r"cannot", r"unable", r"forbidden", r"refused"
        ]
        combined_pattern = "|".join(error_patterns)
        has_error = bool(re.search(combined_pattern, output, re.IGNORECASE))
        return has_error
    
    def interpreter_feedback(self, output: str) -> str:
        """Provide feedback about bash execution"""
        if not output:
            feedback = "No output from bash execution"
            return feedback
        if self.execution_failure_check(output):
            feedback = f"[failure] Bash execution failed:\n{output}"
            return feedback
        else:
            feedback = f"[success] Bash execution successful:\n{output}"
            return feedback