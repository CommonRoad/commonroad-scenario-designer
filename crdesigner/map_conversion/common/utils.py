
def generate_unique_id(set_id: int = None) -> int:
    """
    Generates unique ID using a function counter.

    :param set_id ID which should be set.
    :return: new unique ID

    """
    if not hasattr(generate_unique_id, "counter"):
        generate_unique_id.counter = 0  # it doesn't exist yet, so initialize it
    if set_id is not None:
        generate_unique_id.counter = set_id
        return generate_unique_id.counter
    generate_unique_id.counter += 1
    return generate_unique_id.counter


def convert_to_new_lanelet_id(old_lanelet_id: str, ids_assigned: dict) -> int:
    """
    Convert the old lanelet ids (format 501.1.-1.-1) to newer, simpler ones (100, 101 etc.). Do this by consecutively
    assigning numbers, starting at 100, to the old_lanelet_id strings. Save the assignments in the dict which is passed
    to the function as ids_assigned.

    :param old_lanelet_id: Old id with format '501.1.-1.-1'
    :type old_lanelet_id: str
    :param ids_assigned: Dict with all previous assignments
    :type ids_assigned: dict
    :return: The new lanelet id
    :rtype: int
    """

    starting_lanelet_id = 100

    if old_lanelet_id in ids_assigned.keys():
        new_lanelet_id = ids_assigned[old_lanelet_id]
    else:
        try:
            new_lanelet_id = generate_unique_id()
        except ValueError:
            new_lanelet_id = starting_lanelet_id
        ids_assigned[old_lanelet_id] = new_lanelet_id

    return new_lanelet_id
