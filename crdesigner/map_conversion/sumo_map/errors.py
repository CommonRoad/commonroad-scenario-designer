class NetError(Exception):
    """
    Exception raised if there is no net-file or multiple net-files.

    """

    def __init__(self, len):
        self.len = len

    def __str__(self):
        if self.len == 0:
            return repr("There is no net-file.")
        else:
            return repr("There are more than one net-files.")


class ScenarioException(Exception):
    pass
