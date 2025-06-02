# Breathless Symphony

![Cover Image](Screenshot%20from%202025-06-02%2013-40-55.png)

Autonomous Agentic Framework

## Features

*   **Directory Structure Management**: Automatically creates the necessary directories (`core`, `agents`, `tools`, `prompts`) for organizing the project.
*   **Prompt Management**: Generates initial prompt files for agents (e.g., `prompts/file_agent.txt`).
*   **Dependency Management**: Creates a `requirements.txt` file with necessary Python packages.
*   **Configuration Handling**: Uses `config.ini` for managing project settings, with sensible defaults provided in `config.py`.

## Getting Started

To get started with this project, follow these steps:

1.  **Ensure Ollama is running**:
    ```bash
    ollama serve
    ```
2.  **Pull a model** (e.g., gemma3:27b):
    ```bash
    ollama pull gemma3:27b
    ```
3.  **Install requirements**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the assistant**:
    ```bash
    python main.py
    ```

## Configuration

The project uses a `config.ini` file to manage configurations. If the file doesn't exist, it will be created with default settings. Key configurations include:

*   `provider_name`: The AI provider (default: `ollama`).
*   `provider_model`: The specific model to use (default: `gemma3:27b`).
*   `provider_server_address`: The address of the provider server (default: `127.0.0.1:11434`).
*   `agent_name`: The name of the assistant (default: `Assistant`).
*   `work_dir`: The working directory for the agent (default: `~/agentic_workspace`).
*   `verbose`: Enable or disable verbose logging (default: `False`).

## Directory Structure

The project uses the following directory structure:

*   `core/`: Contains the core logic of the application.
*   `agents/`: Houses the different AI agents.
*   `tools/`: Includes tools and utilities that agents can use.
*   `prompts/`: Stores prompt templates for the agents.
