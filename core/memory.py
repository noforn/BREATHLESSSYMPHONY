import datetime
import uuid

class Memory:
    """
    Memory management for conversation context and history.
    Based on AgenticSeek's memory system with conversation tracking.
    """
    
    def __init__(self, system_prompt, max_history=50):
        self.system_prompt = system_prompt
        self.messages = [{"role": "system", "content": system_prompt}]
        self.max_history = max_history
        self.session_time = datetime.datetime.now()
        self.session_id = str(uuid.uuid4())
    
    def push(self, role, content):
        """Add a message to conversation history with timestamp"""
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.append({
            'role': role, 
            'content': content, 
            'time': time_str
        })
        
        # Keep only recent messages (but always keep system prompt)
        if len(self.messages) > self.max_history:
            self.messages = [self.messages[0]] + self.messages[-(self.max_history-1):]
        
        return len(self.messages) - 1  # Return index for compatibility
    
    def get(self):
        """Get all messages for LLM in OpenAI format"""
        # Convert to OpenAI format (remove time field for LLM)
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def clear(self):
        """Clear history but keep system prompt"""
        self.messages = [self.messages[0]]
    
    def get_session_info(self):
        """Get session information"""
        return {
            "session_id": self.session_id,
            "session_time": self.session_time,
            "message_count": len(self.messages) - 1  # Exclude system prompt
        }