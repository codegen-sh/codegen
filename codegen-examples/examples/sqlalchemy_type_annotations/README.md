# Enhance SQLAlchemy Type Annotations

This codemod demonstrates how to automatically add type annotations to SQLAlchemy models in your Python codebase. The migration script makes this process simple by handling all the tedious manual updates automatically.

## How the Migration Script Works

The script automates the entire migration process in a few key steps:

1. **Model Detection and Analysis**

   ```python
   codebase = Codebase.from_repo("your/repo")
   for file in codebase.files:
       if "models" not in file.filepath:
           continue
   ```

   - Automatically identifies SQLAlchemy model files
   - Analyzes model structure and relationships
   - Determines required type annotations

1. **Type Annotation Updates**

   ```python
   for column in model.columns:
       if isinstance(column, Column):
           column.edit(to_mapped_column(column))
   ```

   - Converts Column definitions to typed Mapped columns
   - Handles nullable fields with Optional types
   - Preserves existing column configurations

1. **Relationship Transformations**

   ```python
   for rel in model.relationships:
       if isinstance(rel, relationship):
           rel.edit(to_typed_relationship(rel))
   ```

   - Updates relationship definitions with proper typing
   - Converts backref to back_populates
   - Adds List/Optional type wrappers as needed

## Common Migration Patterns

### Column Definitions

```python
# Before
id = Column(Integer, primary_key=True)
name = Column(String)

# After
id: Mapped[int] = mapped_column(primary_key=True)
name: Mapped[str] = mapped_column()
```

### Nullable Fields

```python
# Before
description = Column(String, nullable=True)

# After
description: Mapped[Optional[str]] = mapped_column(nullable=True)
```

### Relationships

```python
# Before
addresses = relationship("Address", backref="user")

# After
addresses: Mapped[List["Address"]] = relationship(back_populates="user")
```

## Complete Example

### Before Migration

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from database import Base


class Publisher(Base):
    __tablename__ = "publishers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    books = relationship("Book", backref="publisher")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    description = Column(String)
    publisher_id = Column(Integer, ForeignKey("publishers.id"))
```

### After Migration

```python
from typing import List, Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Publisher(Base):
    __tablename__ = "publishers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    books: Mapped[List["Book"]] = relationship("Book", back_populates="publisher")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(index=True)
    author: Mapped[str] = mapped_column(index=True)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    publisher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("publishers.id"), nullable=True)
    publisher: Mapped[Optional["Publisher"]] = relationship("Publisher", back_populates="books")
```

## Running the Migration

```bash
# Install Codegen
pip install codegen

# Run the migration
python run.py
```

## Learn More

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy Type Annotations Guide](https://docs.sqlalchemy.org/en/20/orm/typing.html)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
