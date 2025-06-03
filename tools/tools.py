import os
import configparser
from abc import abstractmethod
import re

class Tools:
    """
    Abstract base class for all tools that agents can use.
    """
    
    def __init__(self):
        self.tag = "undefined"
        self.name = "Base Tool"
        self.description = "Base class for tools"
        self.work_dir = self.create_work_dir()
        self.executable_blocks_found = False
        
        os.makedirs(self.work_dir, exist_ok=True)
    
    def create_work_dir(self):
        """Create work directory from config or default"""
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            work_dir = config.get('MAIN', 'work_dir')
            expanded_dir = os.path.expanduser(work_dir)
            return expanded_dir
        except Exception as e:
            default_dir = os.path.expanduser('~/agentic_workspace')
            return default_dir
    
    def get_work_dir(self):
        return self.work_dir
    
    def get_parameter_value(self, block: str, parameter: str) -> str:
        """
        Extract parameter value from a text block.
        Expected format: parameter=value
        """
        
        if not block or not parameter:
            return None
            
        lines = block.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(f"{parameter}="):
                value = line.split('=', 1)[1].strip()
                return value
        
        return None
    
    def load_exec_block(self, llm_text: str) -> tuple:
        """
        Extract code/query blocks from LLM-generated text.
        This is the core of AgenticSeek's block execution system.
        
        Args:
            llm_text (str): The raw text containing code blocks from the LLM
        Returns:
            tuple: (list of extracted code blocks, save path or None)
        """
        
        assert self.tag != "undefined", "Tag not defined"
        
        start_tag = f'```{self.tag}'
        end_tag = '```'
        code_blocks = []
        start_index = 0
        save_path = None

        if start_tag not in llm_text:
            return None, None

        
        block_count = 0
        while True:
            start_pos = llm_text.find(start_tag, start_index)
            if start_pos == -1:
                break

            end_pos = llm_text.find(end_tag, start_pos + len(start_tag))
            if end_pos == -1:
                break
                
            content = llm_text[start_pos + len(start_tag):end_pos].strip()
            
            if ':' in content.split('\n')[0]:
                save_path = content.split('\n')[0].split(':')[1].strip()
                content = content[content.find('\n')+1:]
                
            self.executable_blocks_found = True
            code_blocks.append(content)
            
            start_index = end_pos + len(end_tag)
            block_count += 1
            
        
        return code_blocks, save_path
    
    def save_block(self, blocks, save_path):
        """Save code blocks to file"""
        if save_path is None or not blocks:
            return
        full_path = os.path.join(self.work_dir, save_path)
        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(full_path, 'w') as f:
            content = '\n'.join(blocks)
            f.write(content)

    @abstractmethod
    def execute(self, blocks: list, safety: bool = False) -> str:
        """Execute the tool with given blocks - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def execution_failure_check(self, output: str) -> bool:
        """Check if execution failed - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def interpreter_feedback(self, output: str) -> str:
        """Provide feedback about execution - must be implemented by subclasses"""
        pass