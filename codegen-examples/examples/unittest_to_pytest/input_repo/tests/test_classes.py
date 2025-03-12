# tests/test_classes.py

import unittest
from unittest.mock import Mock
from jj_classes.castle import Castle
from jj_classes.character import Character


class TestCastle(unittest.TestCase):
    """Tests for the Castle class."""

    def setUp(self):
        """Set up a test castle."""
        self.castle = Castle("Test Castle")

    def test_castle_name(self):
        """Test that the castle name is set correctly."""
        self.assertEqual(self.castle.name, "Test Castle")

    def test_castle_boss(self):
        """Test that the default boss is Bowser."""
        self.assertEqual(self.castle.boss, "Bowser")

    def test_castle_world(self):
        """Test that the default world is Grass Land."""
        self.assertEqual(self.castle.world, "Grass Land")

    def test_has_access_granted(self):
        """Test that access is granted for the correct powerup."""
        character = Mock(powerup="Super Mushroom")
        self.assertTrue(self.castle.has_access(character))

    def test_has_access_denied(self):
        """Test that access is denied for an incorrect powerup."""
        character = Mock(powerup="Starman")
        self.assertFalse(self.castle.has_access(character))

    def test_empty_name_raises_error(self):
        """Test that an empty castle name raises a ValueError."""
        with self.assertRaises(ValueError):
            Castle("")


class TestCharacter(unittest.TestCase):
    """Tests for the Character class."""

    def setUp(self):
        """Set up a test character."""
        self.character = Character("Mario")

    def test_character_name(self):
        """Test that the character name is set correctly."""
        self.assertEqual(self.character.name, "Mario")

    def test_default_powerup(self):
        """Test that the default powerup is None."""
        self.assertIsNone(self.character.powerup)

    def test_set_powerup(self):
        """Test setting a powerup."""
        self.character.powerup = "Fire Flower"
        self.assertEqual(self.character.powerup, "Fire Flower")

    def test_empty_name_raises_error(self):
        """Test that an empty character name raises a ValueError."""
        with self.assertRaises(ValueError):
            Character("")


class TestCastleAndCharacter(unittest.TestCase):
    """Tests for the interaction between Castle and Character."""

    def setUp(self):
        """Set up a test castle and character."""
        self.castle = Castle("Test Castle")
        self.character = Character("Mario")

    def test_character_has_access(self):
        """Test that a character with the correct powerup has access."""
        self.character.powerup = "Super Mushroom"
        self.assertTrue(self.castle.has_access(self.character))

    def test_character_denied_access(self):
        """Test that a character with the wrong powerup is denied access."""
        self.character.powerup = "Starman"
        self.assertFalse(self.castle.has_access(self.character))


if __name__ == "__main__":
    unittest.main()
