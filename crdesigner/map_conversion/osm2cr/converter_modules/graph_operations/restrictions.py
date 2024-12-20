"""
This Module provides a restriction class which can be used to parse OSM restrictions.
These are used later in the lane linking step
"""

from typing import Optional, Set

known_restrictions = {"no_left_turn", "no_right_turn", "no_straight_on"}


def parse_restriction(restriction: str) -> Optional[Set[str]]:
    """
    parses a restriction tag to a set of defined restrictions:
    {"no_right_turn", "no_straight_on", "no_left_turn"}

    :param restriction: the string of the restriction tag
    :return: the restrictions in structured format
    """
    if restriction in known_restrictions:
        return {restriction}
    else:
        if restriction == "only_left_turn":
            return {"no_right_turn", "no_straight_on"}
        elif restriction == "only_right_turn":
            return {"no_left_turn", "no_straight_on"}
        elif restriction == "only_straight_on":
            return {"no_left_turn", "no_right_turn"}
        elif restriction == "no_u_turn":
            # u-turns are not implemented yet
            # TODO impelement u turns
            pass
        # return connectivity without modifications
        elif restriction.startswith("connectivity"):
            return {str(restriction)}
        else:
            print("unknown restriction: " + restriction)
            return None


class Restriction:
    def __init__(
        self,
        from_edge_id: int,
        via_element_id: int,
        via_element_type: str,
        to_edge_id: int,
        restriction: str,
    ):
        """
        :param from_edge_id: id of the edge the restriction starts
        :param via_element_id: id if the element in the way of the restriction
        :param via_element_type: type of the via element
        :param to_edge_id: id of the edge at which the restriction ends
        :param restriction: type of the restriction
        """
        self.restriction: Set[str] = parse_restriction(restriction)
        self.from_edge_id = from_edge_id
        self.via_element_id = via_element_id
        self.via_element_type = via_element_type
        self.to_edge_id = to_edge_id
        self.from_edge = None
        self.to_edge = None
        self.via_element = None
