class Domain:
    """
    Class representing a domain.
    """

    def __init__(self, domain_id: str):
        """
        Constructor.

        :param domain_id: Domain ID.
        """
        self._domain_id = domain_id

    @property
    def domain_id(self):
        return self._domain_id

    @domain_id.setter
    def domain_id(self, name: str):
        self._domain_id = name

    def to_string(self) -> str:
        """
        Converts domain to string representation.

        :return: String.
        """
        return self._domain_id
