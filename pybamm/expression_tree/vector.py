#
# Vector class
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
import pybamm


class Vector(pybamm.Symbol):
    """
    Parameters
    ----------
    entries : :class:`numpy.array`
        Entries of the vector
    """

    def __init__(self, entries, name=None, parent=None):
        super().__init__(name, parent)
        self._entries = entries
        self.n = entries.size

    def evaluate(self, y=None):
        return self._entries
