# Enhanced version of main.py
# This adds scope command examples and help text

import asyncio
import os
import sys
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core.ollama_provider import OllamaProvider
from core.orchestrator import Orchestrator
from core.ui import ui
from agents.file_agent import FileAgent
from agents.recon_agent import ReconAgent
from agents.web_search_agent import WebSearchAgent

async def main():
    # Clear screen and show header
    ui.clear_screen()
    ui.header("BreathlessSymphony", "Autonomous Penetration Testing Framework")
    
    ui.system_message("Initializing system components...")
    
    # Load configuration
    config = Config()
    
    # Create work directory
    work_dir = config.get('MAIN', 'work_dir')
    work_dir = os.path.expanduser(work_dir)
    os.makedirs(work_dir, exist_ok=True)
    ui.status(f"Work directory: {work_dir}", "info")
    
    # Initialize Ollama provider
    provider = OllamaProvider(
        model=config.get('MAIN', 'provider_model'),
        server_address=config.get('MAIN', 'provider_server_address'),
        verbose=config.getboolean('MAIN', 'verbose')
    )
    ui.status(f"Model loaded: {provider.model}", "info")
    
    # Test Ollama connection
    ui.thinking("Testing Ollama connection...")
    try:
        test_response = provider.respond([{"role": "user", "content": "Hello"}])
        if "Error" in test_response:
            ui.error_box("Ollama Connection Failed", 
                        f"{test_response}\n\nMake sure Ollama is running: ollama serve")
            return
        ui.status("Ollama connection established", "success")
    except Exception as e:
        ui.error_box("Cannot Connect to Ollama", 
                    f"Error: {e}\n\nMake sure Ollama is running: ollama serve")
        return
    
    # Create agents
    ui.system_message("Initializing specialized agents...")
    agents = [
        FileAgent(
            name="File Operative",
            prompt_path="prompts/file_agent.txt", 
            provider=provider,
            work_dir=work_dir,
            verbose=config.getboolean('MAIN', 'verbose')
        ),
        ReconAgent(
            name="Recon Specialist", 
            prompt_path="prompts/recon_agent.txt",
            provider=provider,
            work_dir=work_dir,
            verbose=config.getboolean('MAIN', 'verbose')
        ),
        WebSearchAgent(
            name="Web Intelligence",
            prompt_path="prompts/web_search_agent.txt",
            provider=provider,
            work_dir=work_dir,
            verbose=config.getboolean('MAIN', 'verbose')
        )
    ]
    
    # Create orchestrator with BreathlessSymphony name
    orchestrator = Orchestrator(
        provider=provider,
        agents=agents,
        agent_name="BreathlessSymphony"
    )
    
    ui.separator()
    ui.status("All systems operational", "success")
    ui.status("Agents loaded: File Operative, Recon Specialist, Research Agent", "info")
    ui.status("NEW: Scope tracking enabled for penetration testing", "info")
    ui.separator(thin=True)
    
    # Show example commands with scope management
    examples = [
        # Scope management examples
        "show scope",
        "add 192.168.1.1 to scope",
        "clear scope",
        "",
        # Operation examples with scope context
        "List the files in my directory",
        "Conduct reconnaissance on target.com", 
        "Perform a light port scan on 192.168.1.0/24",
        "Search for CVE-2023-1234 exploits",
        "Search for Apache 2.4.49 vulnerabilities",
    ]
    
    print(f"{ui.colors['dim']}Example commands:{ui.colors['reset']}")
    for example in examples:
        if example == "":
            print()
        else:
            print(f"{ui.colors['dim']}  • {example}{ui.colors['reset']}")
    
    ui.footer_help()
    
    # Main conversation loop
    while True:
        try:
            user_input = ui.user_input()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("")
                ui.status("Terminating session", "info")
                if not orchestrator.memory.scope.is_empty():
                    ui.status("Scope data cleared", "warning")
                print(f"{ui.colors['success']}\nSee you next time!{ui.colors['reset']}")
                print(f"{ui.colors['dim']}Session ended{ui.colors['reset']}")
                break
            
            if user_input.lower() == 'clear':
                ui.clear_screen()
                ui.header("BreathlessSymphony", "Autonomous Penetration Testing Framework")
                ui.footer_help()
                continue
                
            if user_input.lower() == 'help':
                ui.separator()
                help_commands = [
                    "quit/exit/bye - Exit the program",
                    "clear - Clear the screen", 
                    "help - Show this help message",
                    "",
                    "Scope Management (NEW):",
                    "  scope/show scope - Display current penetration test scope",
                    "  add <target> to scope - Add IP/domain/network to scope",
                    "  remove <target> from scope - Remove target from scope", 
                    "  clear scope - Clear all targets from scope",
                    "",
                    "Agent capabilities:",
                    "  File operations: create, read, search, bash commands",
                    "  Reconnaissance: nmap, dig, whois, network scanning",
                    "  Web search: find information, exploits, CVEs, research",
                    "",
                    "Penetration Testing Workflow:",
                    "  1. Add targets to scope: 'add 192.168.1.1 to scope'",
                    "  2. Reconnaissance: 'scan the targets in scope'",
                    "  3. Search exploits: 'find exploits for Apache 2.4.49'",
                    "  4. Agents automatically focus on scoped targets"
                ]
                for cmd in help_commands:
                    if cmd == "":
                        print()
                    else:
                        print(f"{ui.colors['info']}  {cmd}{ui.colors['reset']}")
                ui.separator(thin=True)
                continue
            
            if not user_input:
                continue
            
            # Process request and time it
            start_time = time.time()
            response = await orchestrator.process(user_input)
            end_time = time.time()
            thinking_time = end_time - start_time
            
            ui.agent_response("BreathlessSymphony", response, thinking_time)
            
        except KeyboardInterrupt:
            print()
            ui.status("Session interrupted", "warning")
            ui.system_message("Terminating...")
            break
        except Exception as e:
            ui.error_box("Unexpected Error", str(e))

if __name__ == "__main__":
    asyncio.run(main())