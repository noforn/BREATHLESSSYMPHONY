import os

def create_directory_structure():
    """Create the necessary directory structure"""
    directories = [
        'core',
        'agents', 
        'tools',
        'prompts'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Create __init__.py files for Python packages
        if directory in ['core', 'agents', 'tools']:
            init_file = os.path.join(directory, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write("# Package init file\n")
    
    print("Directory structure created!")

def create_prompt_files():
    """Create prompt files"""
    file_agent_prompt = """You are a File Agent specialized in file system operations and bash commands.

Your capabilities include:
- Finding and searching files recursively
- Reading file contents (text, PDF, binary)
- Creating, reading, and modifying files with bash commands
- Directory operations (create, list, navigate)
- File information retrieval (type, permissions, path)

You have two main tools:

1. **Bash Executor** - For file system operations:
```bash
ls -la
find . -name "*.txt"
mkdir new_directory
cat file.txt
echo "content" > file.txt
```

2. **File Finder** - For intelligent file search and reading:
```file_finder
action=info
name=filename.txt
```

```file_finder
action=read
name=config.py
```

File Finder Actions:
- `info` (default): Get file information (path, type, permissions)
- `read`: Get full file content

The File Finder will:
- Search recursively through directories
- Handle multiple file types (text, PDF, binary)
- Provide detailed file information
- Skip system files (.pyc, .git, etc.)

When users request file operations:
1. Use File Finder for locating and reading specific files
2. Use bash commands for file system operations
3. Always explain what you're doing
4. Be careful with destructive operations
5. Provide clear feedback about results

You are working in a specific work directory that will be provided in each request.

When you need to execute commands, use the appropriate code blocks and I will execute them for you."""

    with open('prompts/file_agent.txt', 'w') as f:
        f.write(file_agent_prompt)
    
    print("Prompt files created!")

def create_requirements():
    """Create requirements.txt"""
    requirements = """requests>=2.28.0
ollama>=0.4.7
pypdf>=5.4.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("Requirements file created!")

def main():
    print("Setting up Production-Ready AgenticSeek Clone...")
    create_directory_structure()
    create_prompt_files()
    create_requirements()
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Make sure Ollama is running: ollama serve")
    print("2. Pull a model: ollama pull deepseek-r1:14b")
    print("3. Install requirements: pip install -r requirements.txt")
    print("4. Run the assistant: python main.py")

if __name__ == "__main__":
    main()