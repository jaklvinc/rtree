from enum import Enum


class RTreeSplitType(Enum):
    BRUTE_FORCE = 1
    QUADRATIC = 2
    LINEAR = 3

    @classmethod
    def from_str(cls, value: str):
        if value == 'bruteforce':
            return cls.BRUTE_FORCE

        if value == 'quadratic':
            return cls.QUADRATIC

        if value == 'linear':
            return cls.LINEAR

        return None

    def to_str(self):
        return self.name.lower()
