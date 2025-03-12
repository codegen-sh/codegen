# Unittest to Pytest Migration Example

This codemod demonstrates how to automatically migrate `unittest` test suites to `pytest` using Codegen. The migration script simplifies the process by handling all the tedious manual updates automatically.

## How the Migration Script Works

The script automates the entire migration process in a few key steps:

1. **Convert Test Classes and Setup Methods**

   ```python
   # From:
   class TestUsers(unittest.TestCase):
       def setUp(self):
           self.db = setup_test_db()

       def test_create_user(self):
           user = self.db.create_user("test")
           self.assertEqual(user.name, "test")


   # To:
   @pytest.fixture
   def db():
       db = setup_test_db()
       yield db


   def test_create_user(db):
       user = db.create_user("test")
       assert user.name == "test"
   ```

   - Converts `unittest.TestCase` classes to standalone functions
   - Replaces `setUp` methods with `pytest` fixtures

1. **Update Assertions**

   ```python
   # From:
   def test_validation(self):
       self.assertTrue(is_valid("test"))
       self.assertEqual(count_items(), 0)
       self.assertRaises(ValueError, parse_id, "invalid")


   # To:
   def test_validation():
       assert is_valid("test")
       assert count_items() == 0
       with pytest.raises(ValueError):
           parse_id("invalid")
   ```

   - Replaces `unittest` assertions with `pytest` assertions
   - Uses `pytest.raises` for exception testing

1. **Convert Test Discovery**

   ```python
   # From:
   if __name__ == "__main__":
       unittest.main()

   # To:
   # Remove unittest.main() and rename files to test_*.py
   ```

   - Removes `unittest.main()` calls
   - Ensures files are named for `pytest` discovery

1. **Modernize Fixtures**

   ```python
   # From:
   @classmethod
   def setUpClass(cls):
       cls.conn = create_db()


   # To:
   @pytest.fixture(scope="session")
   def conn():
       return create_db()
   ```

   - Converts class-level setup to session-scoped fixtures

## Running the Migration

```bash
# Install Codegen
pip install codegen

# Run the migration
python run.py
```

The script will process all Python test files in the `repo-before` directory and apply the transformations in the correct order.

## Understanding the Code

- `run.py` - The migration script
- `input_repo/` - Sample `unittest` test suite to migrate

## Learn More

- [Full Tutorial](https://docs.codegen.com/tutorials/unittest-to-pytest)
- [pytest Documentation](https://docs.pytest.org/)
- [unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
