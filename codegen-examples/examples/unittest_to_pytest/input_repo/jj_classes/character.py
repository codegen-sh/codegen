# jj_classes/character.py


class Character:
    """Defines the Character class."""

    def __init__(self, name):
        """Initialize the character."""
        if not name:
            raise ValueError("Character name cannot be empty.")
        self._name = name
        self._powerup = None

    @property
    def name(self):
        return self._name

    @property
    def powerup(self):
        return self._powerup

    @powerup.setter
    def powerup(self, value):
        self._powerup = value
