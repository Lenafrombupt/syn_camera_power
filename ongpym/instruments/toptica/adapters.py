from pymeasure.adapters import VISAAdapter


class TopticaAdapter(VISAAdapter):
    """ Provides a :class:`SerialAdapter` with the specific read command to account
    for the Scheme programming language.
    :param port: A string representing the serial port
    """

    def __init__(self, port, **kwargs):
        super(TopticaAdapter, self).__init__(
            port, **kwargs

        )

    def ask(self, command):
        """ Writes the command to the instrument and returns the resulting
        ASCII response

        :param command: SCPI command string to be sent to the instrument
        :returns: String ASCII response of the instrument
        """
        self.connection.write(command)
        self.connection.read()
        result = self.connection.read()
        return result

    def write(self, command):
        """ Writes a command to the instrument

        :param command: SCPI command string to be sent to the instrument
        """
        self.connection.write(command)
        try:
            while True:
                self.connection.read_raw()
        except ConnectionError:
            pass
