
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
