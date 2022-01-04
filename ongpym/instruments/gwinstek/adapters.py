from pymeasure.adapters import SerialAdapter


class GWInstekAdapter(SerialAdapter):
    def read(self):
        """ Reads until the buffer is empty and returns the resulting
        ASCII respone

        :returns: String ASCII response of the instrument.
        """
        # return b"\n".join(self.connection.readline()).decode('ascii')
        return self.connection.readline().decode()
