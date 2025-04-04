"""
Document model for storing context documents.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Document model for storing context documents."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    type: str  # "requirement", "context", "plan", etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def update_content(self, content: str) -> None:
        """Update the document content."""
        self.content = content
        self.updated_at = datetime.now().isoformat()
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update the document metadata."""
        self.metadata.update(metadata)
        self.updated_at = datetime.now().isoformat()


class DocumentList(BaseModel):
    """List of documents."""
    
    documents: List[Document] = Field(default_factory=list)
    
    def add_document(self, document: Document) -> None:
        """Add a document to the list."""
        self.documents.append(document)
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Get a document by its ID."""
        for document in self.documents:
            if document.id == document_id:
                return document
        return None
    
    def get_documents_by_type(self, document_type: str) -> List[Document]:
        """Get all documents of a specific type."""
        return [doc for doc in self.documents if doc.type == document_type]
    
    def remove_document(self, document_id: str) -> bool:
        """Remove a document by its ID."""
        for i, document in enumerate(self.documents):
            if document.id == document_id:
                self.documents.pop(i)
                return True
        return False
    
    def save_to_file(self, filepath: str) -> None:
        """Save the document list to a file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.json(indent=2))
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "DocumentList":
        """Load a document list from a file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.parse_obj(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()