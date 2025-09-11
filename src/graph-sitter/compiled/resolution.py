"""
Fallback Python implementation of compiled resolution module.
This provides basic functionality for testing when Cython modules aren't compiled.
"""
from typing import Generic, TypeVar, List, Optional
from enum import Enum

T = TypeVar('T')

class UsageKind(Enum):
    """Enum for different kinds of symbol usage"""
    READ = "read"
    WRITE = "write"
    CALL = "call"
    REFERENCE = "reference"
    DEFINITION = "definition"

class ResolutionStack(Generic[T]):
    """Simple resolution stack implementation"""
    
    def __init__(self):
        self._stack: List[T] = []
    
    def push(self, item: T) -> None:
        self._stack.append(item)
    
    def pop(self) -> Optional[T]:
        if self._stack:
            return self._stack.pop()
        return None
    
    def peek(self) -> Optional[T]:
        if self._stack:
            return self._stack[-1]
        return None
    
    def is_empty(self) -> bool:
        return len(self._stack) == 0
    
    def __len__(self) -> int:
        return len(self._stack)
    
    def __iter__(self):
        return iter(self._stack)
    
    def __class_getitem__(cls, item):
        """Support for generic type subscripting"""
        return cls

class Resolution:
    """Basic resolution implementation"""
    
    def __init__(self, name: str, usage_kind: UsageKind = UsageKind.REFERENCE):
        self.name = name
        self.usage_kind = usage_kind
    
    def __repr__(self):
        return f"Resolution(name='{self.name}', usage_kind={self.usage_kind})"
