# jj_classes/castle.py


class Castle:
    """Defines the Castle class."""

    def __init__(self, name):
        """Initialize the castle."""
        if not name:
            raise ValueError("Castle name cannot be empty.")
        self._name = name
        self._boss = "Bowser"
        self._world = "Grass Land"

    def has_access(self, character):
        """Check if a character has access to the castle."""
        return character.powerup == "Super Mushroom"

    @property
    def name(self):
        return self._name

    @property
    def boss(self):
        return self._boss

    @property
    def world(self):
        return self._world
