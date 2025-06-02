# This is the same content as the first artifact "Enhanced CLI UI Module"
# Save this file as: core/ui.py

import os
import sys
from datetime import datetime

try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback - no colors
    class MockColor:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = MockColor()

class BreathlessUI:
    """
    Stealth-themed CLI interface for BreathlessSymphony
    Dark, covert aesthetic with muted colors
    """
    
    def __init__(self):
        self.width = self._get_terminal_width()
        self.readline_available = READLINE_AVAILABLE
        
        if self.readline_available:
            self.history_file = os.path.expanduser("~/.breathless_history")
            if os.path.exists(self.history_file):
                try:
                    readline.read_history_file(self.history_file)
                except Exception as e:
                    # Could log this error if a logging mechanism exists
                    pass # Ignore if history can't be read

        # Stealth color scheme - muted, covert tones
        if COLORAMA_AVAILABLE:
            self.colors = {
                'primary': Fore.CYAN,           # Muted cyan for agent
                'secondary': Fore.LIGHTBLACK_EX, # Dark gray for borders
                'success': Fore.GREEN,          # Muted green for success
                'warning': Fore.YELLOW,         # Yellow for warnings  
                'error': Fore.RED,              # Red for errors
                'info': Fore.BLUE,              # Blue for info
                'text': Fore.WHITE,             # White for main text
                'dim': Fore.LIGHTBLACK_EX,      # Dim gray for secondary text
                'reset': Style.RESET_ALL
            }
        else:
            self.colors = {k: "" for k in ['primary', 'secondary', 'success', 'warning', 'error', 'info', 'text', 'dim', 'reset']}
    
    def _get_terminal_width(self):
        """Get terminal width, fallback to 80"""
        try:
            return os.get_terminal_size().columns
        except:
            return 80
    
    def _make_line(self, char="─", color=None):
        """Create a horizontal line"""
        color_code = self.colors.get(color, "") if color else ""
        return f"{color_code}{char * self.width}{self.colors['reset']}"
    
    def header(self, title, subtitle=None):
        """Display application header"""
        print()
        print(self._make_line("═", "secondary"))
        
        # Center the title
        title_line = f" {title} "
        padding = (self.width - len(title_line)) // 2
        print(f"{self.colors['secondary']}{'═' * padding}{self.colors['primary']}{title_line}{self.colors['secondary']}{'═' * padding}{self.colors['reset']}")
        
        if subtitle:
            sub_line = f" {subtitle} "
            sub_padding = (self.width - len(sub_line)) // 2
            print(f"{self.colors['secondary']}{'─' * sub_padding}{self.colors['dim']}{sub_line}{self.colors['secondary']}{'─' * sub_padding}{self.colors['reset']}")
        
        print(self._make_line("═", "secondary"))
        print()
    
    def status(self, message, status_type="info"):
        """Display status message with appropriate coloring"""
        color = self.colors.get(status_type, self.colors['text'])
        prefix_map = {
            'success': '[+]',
            'error': '[!]',
            'warning': '[*]',
            'info': '[i]'
        }
        prefix = prefix_map.get(status_type, '[·]')
        print(f"{color}{prefix} {message}{self.colors['reset']}")
    
    def system_message(self, message):
        """Display system/startup messages"""
        print(f"{self.colors['dim']}[SYS] {message}{self.colors['reset']}")
    
    def separator(self, thin=False):
        """Display separator line"""
        char = "─" if thin else "━"
        print(self._make_line(char, "secondary"))
    
    def user_input(self, prompt="You"):
        """Get user input with styled prompt"""
        prompt_text = f"{self.colors['text']}{prompt}: {self.colors['reset']}"
        try:
            user_command = input(prompt_text).strip()
            if self.readline_available:
                try:
                    readline.write_history_file(self.history_file)
                except Exception as e:
                    # Could log this error if a logging mechanism exists
                    pass # Ignore if history can't be written
            return user_command
        except Exception as e:
            self.status(f"Error in input: {e}", "error")
            return ""
    
    def agent_response(self, agent_name, message, thinking_time=None):
        """Display agent response with formatting"""
        print()
        
        # Agent header with optional thinking time
        if thinking_time:
            time_info = f" ({thinking_time:.1f}s)"
        else:
            time_info = ""
            
        header = f"[{agent_name}]{time_info}"
        print(f"{self.colors['primary']}{header}{self.colors['reset']}")
        print(f"{self.colors['secondary']}{'─' * len(header)}{self.colors['reset']}")
        
        # Message content with proper wrapping
        self._print_wrapped(message)
        print()
    
    def _print_wrapped(self, text, indent=0):
        """Print text with word wrapping"""
        words = text.split()
        current_line = " " * indent
        line_length = indent
        
        for word in words:
            if line_length + len(word) + 1 > self.width - 2:
                print(f"{self.colors['text']}{current_line}{self.colors['reset']}")
                current_line = " " * indent + word
                line_length = indent + len(word)
            else:
                if current_line.strip():
                    current_line += " " + word
                    line_length += len(word) + 1
                else:
                    current_line += word
                    line_length += len(word)
        
        if current_line.strip():
            print(f"{self.colors['text']}{current_line}{self.colors['reset']}")
    
    def tool_execution(self, tool_name, block_count):
        """Display tool execution message"""
        print(f"{self.colors['info']}[EXEC] Running {block_count} {tool_name} blocks...{self.colors['reset']}")
    
    def thinking(self, message="Processing..."):
        """Display thinking/processing message"""
        print(f"{self.colors['dim']}[PROC] {message}{self.colors['reset']}")
    
    def error_box(self, title, message):
        """Display error in a box format"""
        print()
        print(self._make_line("─", "error"))
        print(f"{self.colors['error']} ERROR: {title} {self.colors['reset']}")
        print(self._make_line("─", "error"))
        self._print_wrapped(message, indent=2)
        print(self._make_line("─", "error"))
        print()
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def footer_help(self):
        """Display help footer"""
        print(self._make_line("─", "secondary"))
        help_text = "Type 'bye' to exit | 'clear' to clear screen | 'help' for commands"
        print(f"{self.colors['dim']}{help_text}{self.colors['reset']}")
        print()

# Global UI instance
ui = BreathlessUI()