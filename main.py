import asyncio
import os
import sys
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core.ollama_provider import OllamaProvider
from core.orchestrator import Orchestrator  # Using the improved orchestrator
from core.ui import ui
from agents.file_agent import FileAgent
from agents.recon_agent import ReconAgent
from agents.web_search_agent import WebSearchAgent
from agents.exploit_agent import ExploitAgent

async def main():
    # Clear screen and show header
    ui.clear_screen()
    ui.header("BreathlessSymphony", "Autonomous Penetration Testing Framework v2.0")
    
    ui.system_message("Initializing enhanced intent-based routing system...")
    
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
        ),
        ExploitAgent(
            name="Exploit Specialist",
            prompt_path="prompts/exploit_agent.txt",
            provider=provider,
            work_dir=work_dir,
            verbose=config.getboolean('MAIN', 'verbose')
        )
    ]
    
    # Create orchestrator with enhanced routing
    orchestrator = Orchestrator(
        provider=provider,
        agents=agents,
        agent_name="BreathlessSymphony"
    )
    
    ui.separator()
    ui.status("Enhanced intent-based routing system operational", "success")
    ui.status("Agents: File Operative, Recon Specialist, Web Intelligence, Exploit Specialist", "info")
    ui.status("NEW: Intelligent intent analysis replaces keyword matching", "info")
    ui.status("NEW: Multi-agent coordination for complex workflows", "info")
    ui.separator(thin=True)
    
    # Show enhanced examples demonstrating intelligent routing
    examples = [
        "# Intent-Based Routing Examples:",
        "",
        "# General conversation (handled directly):",
        "How are you doing today?",
        "What can you help me with?",
        "",
        "# Web research (web_search_agent):",
        "What are the latest cybersecurity trends in 2025?",
        "Find information about CVE-2024-1234",
        "Research Apache HTTP Server vulnerabilities",
        "",
        "# File operations (file_agent):",
        "Show me the contents of my config directory",
        "Create a new script file called scanner.py",
        "Find all log files modified in the last week",
        "",
        "# Network reconnaissance (recon_agent):",
        "Perform a port scan on 192.168.1.1",
        "Enumerate services on the target network",
        "Check if ports 80 and 443 are open on example.com",
        "",
        "# Exploitation workflow (exploit_agent):",
        "Download exploits for Apache path traversal",
        "Find and execute CVE-2021-44228 proof of concept",
        "Set up a listener and run reverse shell exploit",
        "",
        "# Multi-agent workflows (coordinated execution):",
        "Scan network 192.168.1.0/24 and save results to a file",
        "Research CVE-2023-1234, download exploits, and test them",
        "Find the latest Log4j vulnerabilities and check my system",
        "Perform reconnaissance on target.com and document findings"
    ]
    
    print(f"{ui.colors['dim']}Enhanced Examples (Intent-Based Routing):{ui.colors['reset']}")
    for example in examples:
        if example.startswith("#"):
            print(f"{ui.colors['info']}{example}{ui.colors['reset']}")
        elif example == "":
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
                    ui.status("Scope data will be cleared on exit", "warning")
                print(f"{ui.colors['success']}\nSee you next time!{ui.colors['reset']}")
                print(f"{ui.colors['dim']}Session ended{ui.colors['reset']}")
                break
            
            if user_input.lower() == 'clear':
                ui.clear_screen()
                ui.header("BreathlessSymphony", "Autonomous Penetration Testing Framework v2.0")
                ui.footer_help()
                continue
                
            if user_input.lower() == 'help':
                ui.separator()
                help_commands = [
                    "quit/exit/bye - Exit the program",
                    "clear - Clear the screen", 
                    "help - Show this help message",
                    "status - Show current system status",
                    "",
                    "INTELLIGENT ROUTING:",
                    "  The system now uses AI to understand your intent instead of keywords",
                    "  Simply describe what you want to accomplish naturally",
                    "",
                    "AUTOMATIC AGENT SELECTION:",
                    "  • Web research: 'Find information about...', 'What are the latest...'",
                    "  • File operations: 'Show me files...', 'Create a script...'", 
                    "  • Network recon: 'Scan the network...', 'Check if port 80...'",
                    "  • Exploitation: 'Download exploits for...', 'Test CVE-2023...'",
                    "",
                    "MULTI-AGENT WORKFLOWS:",
                    "  Complex tasks automatically use multiple agents:",
                    "  • 'Scan network and save results' → recon + file agents",
                    "  • 'Research CVE and test exploit' → web search + exploit agents",
                    "  • 'Find vulnerabilities and document them' → multiple coordinated agents",
                    "",
                    "SCOPE MANAGEMENT:",
                    "  scope/show scope - Display current penetration test scope",
                    "  add <target> to scope - Add IP/domain/network to scope",
                    "  remove <target> from scope - Remove target from scope", 
                    "  clear scope - Clear all targets from scope",
                    "",
                    "NATURAL LANGUAGE EXAMPLES:",
                    "  Instead of guessing keywords, just ask naturally:",
                    "  'I need to find all configuration files on my system'",
                    "  'Research the latest Apache vulnerabilities for me'",
                    "  'Scan my lab network and create a report'",
                    "  'Find CVE-2023-1234 exploits and test them safely'"
                ]
                for cmd in help_commands:
                    if cmd == "":
                        print()
                    elif cmd.startswith("🧠") or cmd.startswith("🔄") or cmd.startswith("🚀") or cmd.startswith("📋") or cmd.startswith("💡"):
                        print(f"{ui.colors['primary']}{cmd}{ui.colors['reset']}")
                    elif cmd.startswith("  ✅"):
                        print(f"{ui.colors['success']}{cmd}{ui.colors['reset']}")
                    else:
                        print(f"{ui.colors['info']}  {cmd}{ui.colors['reset']}")
                ui.separator(thin=True)
                continue
            
            if user_input.lower() == 'status':
                status = orchestrator.get_status()
                ui.separator()
                ui.status("System Status:", "info")
                for key, value in status.items():
                    print(f"{ui.colors['dim']}  {key}: {value}{ui.colors['reset']}")
                ui.separator(thin=True)
                continue
            
            if not user_input:
                continue
            
            # Process request with enhanced routing and time it
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
    print(f"{ui.colors['info']}🚀 Starting BreathlessSymphony v2.0 with Enhanced Intent Routing...{ui.colors['reset']}")
    asyncio.run(main())
