import datetime
import uuid
from typing import List, Dict

class ScopeManager:
    """
    Fixed ScopeManager with restrictive domain detection to avoid false positives.
    """
    
    def __init__(self):
        self.targets: set = set()
        self.networks: set = set()
        self.domains: set = set()
        self.notes = {}
        
        import re
        import ipaddress
        
        self.ip_pattern = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        )
        self.domain_pattern = re.compile(
            r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        )
        self.network_pattern = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/(?:[0-9]|[1-2][0-9]|3[0-2])\b'
        )
        self.ipaddress = ipaddress
        
        self.exclude_patterns = [
            r'.*\.txt$',           
            r'.*\.log$',           
            r'.*\.xml$',           
            r'.*\.json$',          
            r'.*\.csv$',           
            r'.*\.html?$',         
            r'.*\.php$',           
            r'.*\.js$',            
            r'.*\.css$',           
            r'.*\.py$',            
            r'.*\.sh$',            
            r'.*\.conf$',          
            r'.*\.cfg$',           
            r'.*\.home$',          
            r'.*\.local$',         
            r'.*\.lan$',           
            r'localhost',          
            r'.*\.internal$',      
            r'example\.com',       
            r'example\.org',       
            r'test\.com',          
            r'nmap\.org',          
            r'github\.com',        
            r'exploit-db\.com',    
        ]
    
    def is_excluded_domain(self, domain: str) -> bool:
        """Check if domain should be excluded from auto-detection"""
        import re
        domain_lower = domain.lower()
        
        for pattern in self.exclude_patterns:
            if re.match(pattern, domain_lower):
                return True
        return False
    
    def is_valid_target_domain(self, domain: str) -> bool:
        """Check if domain is a valid target (not a filename or tool reference)"""
        domain_lower = domain.lower().strip()
        
        if len(domain_lower.split('.')) < 2:
            return False
        
        if self.is_excluded_domain(domain_lower):
            return False
        
        tld = domain_lower.split('.')[-1]
        if len(tld) < 2:
            return False
        
        if ('/' in domain_lower or 
            domain_lower.endswith(('.txt', '.log', '.xml', '.json', '.html', '.php', '.js', '.css', '.py', '.sh', '.conf', '.cfg')) or
            '-' in tld): 
            return False
            
        return True
    
    def auto_detect_and_add(self, text: str):
        """Automatically detect and add IPs, domains, networks from text - RESTRICTIVE VERSION"""
        added = []
        
        networks = self.network_pattern.findall(text)
        for network in networks:
            if self.add_network(network):
                added.append(f"Network: {network}")
        
        ips = self.ip_pattern.findall(text)
        for ip in ips:
            skip = False
            for network in networks:
                try:
                    if self.ipaddress.ip_address(ip) in self.ipaddress.ip_network(network, strict=False):
                        skip = True
                        break
                except:
                    pass
            
            if not skip and self.add_target(ip):
                added.append(f"IP: {ip}")
        
        potential_domains = self.domain_pattern.findall(text)
        for domain in potential_domains:
            if (not self.ip_pattern.match(domain) and 
                self.is_valid_target_domain(domain)):
                if self.add_domain(domain):
                    added.append(f"Domain: {domain}")
        
        return added
    
    def add_target(self, target: str) -> bool:
        """Add a single IP target"""
        try:
            self.ipaddress.ip_address(target)
            if target not in self.targets:
                self.targets.add(target)
                return True
        except ValueError:
            pass
        return False
    
    def add_domain(self, domain: str) -> bool:
        """Add a domain target"""
        domain = domain.lower().strip()
        if domain and domain not in self.domains:
            self.domains.add(domain)
            return True
        return False
    
    def add_network(self, network: str) -> bool:
        """Add a network range"""
        try:
            self.ipaddress.ip_network(network, strict=False)
            if network not in self.networks:
                self.networks.add(network)
                return True
        except ValueError:
            pass
        return False
    
    def remove_target(self, target: str) -> bool:
        """Remove target from scope"""
        removed = False
        if target in self.targets:
            self.targets.remove(target)
            removed = True
        if target in self.domains:
            self.domains.remove(target)
            removed = True
        if target in self.networks:
            self.networks.remove(target)
            removed = True
        return removed
    
    def add_note(self, target: str, note: str):
        """Add a note for a specific target"""
        self.notes[target] = note
    
    def get_scope_summary(self) -> str:
        """Get formatted scope summary"""
        if not any([self.targets, self.domains, self.networks]):
            return "No targets in scope"
        
        summary = ["=== CURRENT SCOPE ==="]
        
        if self.targets:
            summary.append(f"IPs ({len(self.targets)}):")
            for ip in sorted(self.targets):
                note = f" - {self.notes[ip]}" if ip in self.notes else ""
                summary.append(f"  • {ip}{note}")
        
        if self.domains:
            summary.append(f"Domains ({len(self.domains)}):")
            for domain in sorted(self.domains):
                note = f" - {self.notes[domain]}" if domain in self.notes else ""
                summary.append(f"  • {domain}{note}")
        
        if self.networks:
            summary.append(f"Networks ({len(self.networks)}):")
            for network in sorted(self.networks):
                note = f" - {self.notes[network]}" if network in self.notes else ""
                summary.append(f"  • {network}{note}")
        
        summary.append("=====================")
        return "\n".join(summary)
    
    def get_all_targets(self):
        """Get all targets as a flat list"""
        return list(self.targets) + list(self.domains) + list(self.networks)
    
    def clear_scope(self):
        """Clear all scope data"""
        self.targets.clear()
        self.domains.clear()
        self.networks.clear()
        self.notes.clear()
    
    def is_empty(self) -> bool:
        """Check if scope is empty"""
        return not any([self.targets, self.domains, self.networks])
    
class Memory:
    """
    Enhanced Memory management with scope tracking for penetration testing.
    Maintains backward compatibility with existing functionality.
    """
    
    def __init__(self, system_prompt, max_history=50):
        self.system_prompt = system_prompt
        self.messages = [{"role": "system", "content": system_prompt}]
        self.max_history = max_history
        self.session_time = datetime.datetime.now()
        self.session_id = str(uuid.uuid4())
        
        self.scope = ScopeManager()
    
    def push(self, role, content, auto_add_to_scope: bool = True):
        """Add a message to conversation history with scope detection"""
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.append({
            'role': role, 
            'content': content, 
            'time': time_str
        })
        
        if auto_add_to_scope and role == 'user':
            detected = self.scope.auto_detect_and_add(content)
            if detected:
                try:
                    from core.ui import ui
                    #for item in detected:
                    #    ui.status(f"Added to scope: {item}", "info")
                except ImportError:
                    pass
        
        if len(self.messages) > self.max_history:
            self.messages = [self.messages[0]] + self.messages[-(self.max_history-1):]
        
        return len(self.messages) - 1
    
    def get(self):
        """Get all messages for LLM in OpenAI format with scope context"""
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
        
        if not self.scope.is_empty():
            scope_context = f"\n\nCURRENT PENETRATION TEST SCOPE:\n{self.scope.get_scope_summary()}\n\nAlways consider the current scope when performing operations. Focus reconnaissance and testing efforts on targets within scope."
            
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] += scope_context
        
        return messages
    
    def clear(self):
        """Clear history but keep system prompt and scope"""
        self.messages = [self.messages[0]]
    
    def get_session_info(self):
        """Get session information including scope"""
        base_info = {
            "session_id": self.session_id,
            "session_time": self.session_time,
            "message_count": len(self.messages) - 1
        }
        
        base_info["scope_targets"] = len(self.scope.get_all_targets())
        base_info["scope_summary"] = self.scope.get_scope_summary() if not self.scope.is_empty() else "No scope set"
        
        return base_info