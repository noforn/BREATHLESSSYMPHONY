import configparser
import os

class Config:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        
        # Default configuration
        default_config = {
            'MAIN': {
                'provider_name': 'ollama',
                'provider_model': 'gemma3:27b',
                'provider_server_address': '127.0.0.1:11434',
                'agent_name': 'Assistant',
                'work_dir': os.path.expanduser('~/agentic_workspace'),
                'verbose': 'False'
            }
        }
        
        # Create config file if it doesn't exist
        if not os.path.exists(config_file):
            self.config.read_dict(default_config)
            with open(config_file, 'w') as f:
                self.config.write(f)
        else:
            self.config.read(config_file)
    
    def get(self, section, key):
        return self.config.get(section, key)
    
    def getboolean(self, section, key):
        return self.config.getboolean(section, key)