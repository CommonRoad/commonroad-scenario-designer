"""
This module provides custom types for an easier type description:
 * **Road_info** stores information about a road
 * **Assumption_info** stores information about the assumptions made when determining the road information
"""

from typing import List, Optional, Tuple

# type to store information about a road
Road_info = Tuple[
    int, int, int, bool, Optional[List[str]], Optional[List[str]], Optional[List[str]]
]
# type to store information about assumptions made
Assumption_info = Tuple[bool, bool, bool]
