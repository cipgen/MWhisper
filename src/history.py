"""
MWhisper Dictation History
Stores and manages recent dictations
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class DictationEntry:
    """Represents a single dictation entry"""
    
    def __init__(
        self,
        text: str,
        timestamp: Optional[str] = None,
        duration: float = 0.0,
        language: str = "unknown"
    ):
        self.text = text
        self.timestamp = timestamp or datetime.now().isoformat()
        self.duration = duration
        self.language = language
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "language": self.language
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DictationEntry':
        """Create from dictionary"""
        return cls(
            text=data.get("text", ""),
            timestamp=data.get("timestamp"),
            duration=data.get("duration", 0.0),
            language=data.get("language", "unknown")
        )
    
    def __str__(self) -> str:
        dt = datetime.fromisoformat(self.timestamp)
        time_str = dt.strftime("%H:%M")
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"[{time_str}] {preview}"


class DictationHistory:
    """Manages dictation history"""
    
    def __init__(self, history_path: Optional[str] = None, max_size: int = 20):
        """
        Initialize history manager.
        
        Args:
            history_path: Path to history file
            max_size: Maximum number of entries to keep
        """
        if history_path:
            self.history_path = Path(history_path)
        else:
            app_dir = Path(__file__).parent.parent
            self.history_path = app_dir / "history.json"
        
        self.max_size = max_size
        self._entries: List[DictationEntry] = []
        self.load()
    
    def load(self) -> bool:
        """Load history from file"""
        try:
            if self.history_path.exists():
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._entries = [
                    DictationEntry.from_dict(entry)
                    for entry in data.get("entries", [])
                ]
                return True
        except Exception as e:
            print(f"Failed to load history: {e}")
        return False
    
    def save(self) -> bool:
        """Save history to file"""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "entries": [entry.to_dict() for entry in self._entries]
            }
            
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Failed to save history: {e}")
            return False
    
    def add(
        self,
        text: str,
        duration: float = 0.0,
        language: str = "unknown"
    ) -> DictationEntry:
        """
        Add a new dictation to history.
        
        Args:
            text: Transcribed text
            duration: Recording duration in seconds
            language: Detected language
        
        Returns:
            Created entry
        """
        entry = DictationEntry(
            text=text,
            duration=duration,
            language=language
        )
        
        # Add to beginning (most recent first)
        self._entries.insert(0, entry)
        
        # Trim to max size
        if len(self._entries) > self.max_size:
            self._entries = self._entries[:self.max_size]
        
        self.save()
        return entry
    
    def get_all(self) -> List[DictationEntry]:
        """Get all entries (most recent first)"""
        return self._entries.copy()
    
    def get_recent(self, count: int = 5) -> List[DictationEntry]:
        """Get recent entries"""
        return self._entries[:count]
    
    def get_by_index(self, index: int) -> Optional[DictationEntry]:
        """Get entry by index"""
        if 0 <= index < len(self._entries):
            return self._entries[index]
        return None
    
    def clear(self) -> None:
        """Clear all history"""
        self._entries = []
        self.save()
    
    def delete(self, index: int) -> bool:
        """Delete entry by index"""
        if 0 <= index < len(self._entries):
            self._entries.pop(index)
            self.save()
            return True
        return False
    
    def set_max_size(self, size: int) -> None:
        """Set maximum history size"""
        self.max_size = size
        if len(self._entries) > size:
            self._entries = self._entries[:size]
            self.save()
    
    def __len__(self) -> int:
        return len(self._entries)
    
    def __iter__(self):
        return iter(self._entries)


# Singleton instance
_history_instance: Optional[DictationHistory] = None


def get_history(history_path: Optional[str] = None, max_size: int = 20) -> DictationHistory:
    """Get or create singleton history instance"""
    global _history_instance
    if _history_instance is None:
        _history_instance = DictationHistory(history_path, max_size)
    return _history_instance
