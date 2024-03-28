import enum


class Symbol(enum.Enum):
    """
    Enum representing the symbols of operators.
    """

    NOT = "!"
    AND = "&"
    OR = "|"
    XOR = "^"
    IMPLICATION = "->"
    EQUIVALENCE = "<->"
    UNIVERSAL = "A"
    EXISTENTIAL = "E"
    COUNTING = "C"
    EQUAL = "="
    UNEQUAL = "!="
    LESS = "<"
    GREATER = ">"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
