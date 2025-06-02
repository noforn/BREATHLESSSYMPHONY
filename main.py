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
    ui.header("BreathlessSymphony", "Autonomous Agentic Framework")
    
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
    ui.separator(thin=True)
    
    # Show example commands
    examples = [
        "List the files in my directory",
        "Create a file called test.txt with hello world", 
        "Conduct reconnaissance on target.com",
        "Perform a light port scan on 192.168.1.1", 
        "Search for current date",
        "Search for exploits affecting Apache 2.4.49",
    ]
    
    print(f"{ui.colors['dim']}Example commands:{ui.colors['reset']}")
    for example in examples:
        print(f"{ui.colors['dim']}  • {example}{ui.colors['reset']}")
    
    ui.footer_help()
    
    # Main conversation loop
    while True:
        try:
            user_input = ui.user_input()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("")
                ui.status("Terminating session", "info")
                print(f"{ui.colors['success']}\nSee you next time!{ui.colors['reset']}")
                print(f"{ui.colors['dim']}Session ended{ui.colors['reset']}")
                break
            
            if user_input.lower() == 'clear':
                ui.clear_screen()
                ui.header("BreathlessSymphony", "Autonomous Agentic Framework")
                ui.footer_help()
                continue
                
            if user_input.lower() == 'help':
                ui.separator()
                help_commands = [
                    "quit/exit/bye - Exit the program",
                    "clear - Clear the screen", 
                    "help - Show this help message",
                    "",
                    "Agent capabilities:",
                    "  File operations: create, read, search, bash commands",
                    "  Reconnaissance: nmap, dig, whois, network scanning",
                    "  Web search: find information, news, research topics"
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