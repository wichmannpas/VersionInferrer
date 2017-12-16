from typing import Union

from backends.software_version import SoftwareVersion
from settings import POSITIVE_MATCH_WEIGHT, NEGATIVE_MATCH_WEIGHT


class Guess:
    """
    A guess during analysis.
    """
    # software_version: SoftwareVersion
    # positive_matches: int
    # negative_matches: int

    def __init__(
            self,
            software_version: SoftwareVersion,
            positive_matches: Union[set, None] = None,
            negative_matches: Union[set, None] = None):
        self.software_version = software_version
        self.positive_matches = set()
        if positive_matches:
            self.positive_matches = positive_matches
        self.negative_matches = set()
        if negative_matches:
            self.negative_matches = negative_matches

    def __lt__(self, other) -> bool:
        return self.strength < other.strength

    def __le__(self, other) -> bool:
        return self.strength <= other.strength

    def __eq__(self, other) -> bool:
        return self.strength == other.strength

    def __ge__(self, other) -> bool:
        return self.strength >= other.strength
    
    def __gt__(self, other) -> bool:
        return self.strength > other.strength

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def __str__(self) -> str:
        return '{} (+{}[{}]-{}[{}])'.format(
            self.software_version,
            len(self.positive_matches),
            self.positive_strength,
            len(self.negative_matches),
            self.negative_strength)

    def serialize(self) -> dict:
        """Serialize into a dict."""
        return {
            'software_version': self.software_version.serialize(),
            'positive_matches': self.positive_matches,
            'negative_matches': self.negative_matches,
        }

    @property
    def negative_strength(self) -> float:
        """The negative strength of the guess."""
        return sum(
            asset.idf_weight
            for asset in self.negative_matches
        )

    @property
    def positive_strength(self) -> float:
        """The positive strength of the guess."""
        return sum(
            asset.idf_weight
            for asset in self.positive_matches
        )

    @property
    def strength(self) -> float:
        """The strength of the guess."""
        return (
            POSITIVE_MATCH_WEIGHT * self.positive_strength +
            NEGATIVE_MATCH_WEIGHT * self.negative_strength
        )
