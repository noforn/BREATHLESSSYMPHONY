import requests
import json
from ollama import Client as OllamaClient
import httpx

class OllamaProvider:
    """
    Handles local and remote Ollama connections with streaming support.
    """
    
    def __init__(self, model, server_address, verbose=False):
        self.model = model
        self.server_address = server_address
        self.host = f"http://{server_address}"
        self.verbose = verbose
        self.client = OllamaClient(host=self.host)
    
    def respond(self, messages, verbose=None):
        """Send messages to Ollama and get response with streaming"""
        if verbose is None:
            verbose = self.verbose
            
        try:
            if verbose:
                print(f"Sending request to {self.host}")
            
            # Use streaming for real-time output
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
            )
            
            thought = ""
            for chunk in stream:
                if verbose:
                    print(chunk["message"]["content"], end="", flush=True)
                thought += chunk["message"]["content"]
            
            if verbose:
                print()  # New line after streaming
            
            return thought
            
        except httpx.ConnectError as e:
            return f"Error: Ollama connection failed at {self.host}. Check if server is running."
        except Exception as e:
            if hasattr(e, 'status_code') and e.status_code == 404:
                print(f"Model {self.model} not found. Downloading...")
                try:
                    self.client.pull(self.model)
                    return self.respond(messages, verbose)
                except Exception as pull_error:
                    return f"Error: Failed to download model {self.model}: {pull_error}"
            return f"Error communicating with Ollama: {e}"
    
    def get_model_name(self):
        """Get the current model name"""
        return self.model
    
    def test_connection(self):
        """Test connection to Ollama server"""
        try:
            response = self.respond([{"role": "user", "content": "Hello"}])
            return not response.startswith("Error:")
        except Exception:
            return False