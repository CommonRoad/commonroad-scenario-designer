def check_string_for_null(txt: str) -> bool:
    """
    @param txt: input string
    @return: boolean value indicating if input string is None, "None" or ""
    """
    return txt in ["", "None", None]


def convert_string_to_float(txt: str) -> float:
    """
    @param txt: input string
    @return: float if input string can be converted to float else 0
    """
    try:
        return float(txt) if txt is not None and txt != "" else 0
    except ValueError:
        return 0
