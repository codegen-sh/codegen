# SQLAlchemy 1.4 to 2.0 Migration Example

[![Documentation](https://img.shields.io/badge/docs-docs.codegen.com-blue)](https://docs.codegen.com/tutorials/sqlalchemy-1.4-to-2.0)

This example demonstrates how to use Codegen to automatically migrate SQLAlchemy 1.4 code to the new 2.0-style query interface. For a complete walkthrough, check out our [tutorial](https://docs.codegen.com/tutorials/sqlalchemy-1.4-to-2.0).

## How the Migration Script Works

The migration script handles four key transformations:

1. **Convert Query to Select**

   ```python
   # From:
   session.query(User).filter_by(name="john").all()

   # To:
   session.execute(select(User).where(User.name == "john")).scalars().all()
   ```

   - Replaces legacy `query()` syntax with modern `select()` statements
   - Updates filter conditions to use explicit comparison operators
   - Adds proper `execute()` and `scalars()` chain

1. **Update Session Execution**

   ```python
   # From:
   users = session.query(User).all()
   first_user = session.query(User).first()

   # To:
   users = session.execute(select(User)).scalars().all()
   first_user = session.execute(select(User)).scalars().first()
   ```

   - Modernizes session query methods with `execute()` pattern
   - Adds proper result handling with `scalars()`
   - Updates common operations like `all()`, `first()`, `one()`

1. **Modernize ORM Relationships**

   ```python
   # From:
   class User(Base):
       addresses = relationship("Address", backref="user")


   # To:
   class User(Base):
       addresses = relationship("Address", back_populates="user", use_list=True)


   class Address(Base):
       user = relationship("User", back_populates="addresses")
   ```

   - Replaces deprecated `backref` with explicit `back_populates`
   - Creates bidirectional relationship definitions
   - Adds `use_list` parameter for collection relationships

1. **Add Type Annotations**

   ```python
   # From:
   class User(Base):
       __tablename__ = "users"
       id = Column(Integer, primary_key=True)
       name = Column(String)
       addresses = relationship("Address")


   # To:
   class User(Base):
       __tablename__ = "users"
       id: Mapped[int] = mapped_column(primary_key=True)
       name: Mapped[str] = mapped_column()
       addresses: Mapped[List["Address"]] = relationship()
   ```

   - Introduces `Mapped[]` type wrappers for all columns
   - Converts `Column()` to `mapped_column()`
   - Handles nullable fields with `Optional[]` types

## Running the Migration

```bash
# Install Codegen
pip install codegen

# Run the migration
python run.py
```

## Learn More

- [Full Tutorial](https://docs.codegen.com/tutorials/sqlalchemy-1.4-to-2.0)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [What's New in SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
