import os
import stat
import mimetypes
from tools.tools import Tools

class FileFinder(Tools):
    """
    A tool that finds files in the directory and returns their information.
    Based on AgenticSeek's FileFinder with parameter parsing and multiple file type support.
    """
    
    def __init__(self):
        super().__init__()
        self.tag = "file_finder"
        self.name = "File Finder"
        self.description = "Finds files in the directory and returns their information."
        
        try:
            from core.ui import ui
            self.ui = ui
        except ImportError:
            self.ui = None
    
    def read_file(self, file_path: str) -> str:
        """Read the content of a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading file: {e}"
        
    def read_arbitrary_file(self, file_path: str, file_type: str) -> str:
        """Read content of file with arbitrary encoding"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith(('image/', 'video/', 'audio/')):
                return "Can't read file type: image, video, or audio files are not supported."
        
        content_raw = self.read_file(file_path)
        if "Error reading file" in content_raw:
            return content_raw
            
        if "text" in file_type or file_type == "Unknown":
            content = content_raw
        elif "pdf" in file_type:
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                content = '\n'.join([pt.extract_text() for pt in reader.pages])
            except ImportError:
                content = "PDF reading not available (install pypdf: pip install pypdf)"
            except Exception as e:
                content = f"Error reading PDF: {e}"
        elif "binary" in file_type:
            try:
                with open(file_path, 'rb') as f:
                    raw_bytes = f.read()
                content = raw_bytes.decode('utf-8', errors='replace')
            except Exception as e:
                content = f"Error reading binary file: {e}"
        else:
            content = content_raw
        return content
    
    def get_file_info(self, file_path: str) -> dict:
        """Get comprehensive information about a file"""
        if os.path.exists(file_path):
            try:
                stats = os.stat(file_path)
                permissions = oct(stat.S_IMODE(stats.st_mode))
                file_type, _ = mimetypes.guess_type(file_path)
                file_type = file_type if file_type else "Unknown"
                content = self.read_arbitrary_file(file_path, file_type)
                
                return {
                    "filename": os.path.basename(file_path),
                    "path": file_path,
                    "type": file_type,
                    "read": content,
                    "permissions": permissions
                }
            except Exception as e:
                return {"filename": os.path.basename(file_path), "error": f"Error accessing file: {e}"}
        else:
            return {"filename": file_path, "error": "File not found"}
    
    def recursive_search(self, directory_path: str, filename: str) -> str:
        """Recursively search for files in directory and subdirectories"""
        excluded_files = [".pyc", ".o", ".so", ".a", ".lib", ".dll", ".dylib", ".git"]
        
        try:
            for root, dirs, files in os.walk(directory_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for f in files:
                    if f is None:
                        continue
                    if any(excluded_file in f for excluded_file in excluded_files):
                        continue
                    if filename.strip().lower() in f.strip().lower():
                        return os.path.join(root, f)
        except Exception as e:
            if self.ui:
                self.ui.status(f"Search error: {e}", "error")
            else:
                print(f"Error during search: {e}")
        
        return None

    def execute(self, blocks: list, safety: bool = False) -> str:
        """
        Execute file finding operation with parameter parsing.
        Expected format:
        action=read
        name=filename.txt
        """
        if not blocks or not isinstance(blocks, list):
            return "Error: No valid blocks provided"

        output = ""
        for block in blocks:
            filename = self.get_parameter_value(block, "name")
            action = self.get_parameter_value(block, "action")
            
            if filename is None:
                output += "Error: No filename provided\n"
                continue
                
            if action is None:
                action = "info"
            
            if self.ui:
                self.ui.thinking(f"Searching for '{filename}'...")
            else:
                print(f"File finder: searching for '{filename}'...")
                
            file_path = self.recursive_search(self.work_dir, filename)
            
            if file_path is None:
                output += f"File: {filename} - not found\n"
                continue
                
            result = self.get_file_info(file_path)
            
            if "error" in result:
                output += f"File: {result['filename']} - {result['error']}\n"
            else:
                if action == "read":
                    output += f"Content of {result['filename']}:\n{result['read']}\n"
                else:
                    output += (f"File: {result['filename']}, "
                              f"found at {result['path']}, "
                              f"File type: {result['type']}\n")
        
        return output.strip()

    def execution_failure_check(self, output: str) -> bool:
        """Check if file finding operation failed"""
        if not output:
            return True
        if "Error" in output or "not found" in output:
            return True
        return False

    def interpreter_feedback(self, output: str) -> str:
        """Provide feedback about file finding operation"""
        if not output:
            return "No output generated from file finder tool"
        
        if self.execution_failure_check(output):
            return f"File Finder failed: {output}"
        else:
            return f"File Finder successful: {output}"