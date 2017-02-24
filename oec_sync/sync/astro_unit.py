from pint import UnitRegistry
from decimal import Decimal
from typing import Tuple
from syncutil import SrcPath
import re


class Quantity:
    """
    Representation of a quantity and associated error in a specific
    unit system.
    """
    # Load unit registry from module resources
    _UR = UnitRegistry()
    _UR.load_definitions(SrcPath.abs('sync/resources/units.txt'))
    NUM_REGEX = re.compile(R'[-+]?\d*\.?\d+([eE][-+]?\d+)?')

    def __init__(self,
                 value: str,
                 unit: str = None,
                 error: Tuple[str, str] = None,
                 is_limit: bool = False):
        """
        Construct a Quantity object.
        :param value: The quantity value.
        :param unit: The unit system.
        :param error: The lower bound and upper bound of error.
        :param is_limit: If set to True, the error tuple represents lower limit
                         and upper limit.
        """
        if not value:
            raise ValueError("Value cannot be empty: " + repr(value))
        value = value.strip()
        if not self._is_num(value):
            raise ValueError("Invalid number: " + repr(value))
        if error and not (self._is_num(error[0]) and self._is_num(error[1])):
            error = None   # errors must be defined in a pair

        if error and not is_limit:
            # error-minus and error-plus pair should be non-negative
            error = (
                str(abs(Decimal(error[0]))),
                str(abs(Decimal(error[1])))
            )

        self.value = value
        self.unit = unit
        self.error = error
        self.is_limit = is_limit

    def __eq__(self, other: 'Quantity'):
        # keep the type quoted ^, class is incomplete at this point

        # value
        if Decimal(self.value) != Decimal(other.value):
            return False
        # unit
        if not self._eq_unit(self.unit, other.unit):
            return False
        return True

    def __repr__(self):
        return "Quantity(" + repr(self.value) + "," + repr(self.unit) + "," + \
               repr(self.error) + "," + repr(self.is_limit) + ")"

    @classmethod
    def _is_num(cls, value: str):
        """
        Returns whether a string value is a valid value
        :param value: a string representing a number
        """
        return value is not None and bool(cls.NUM_REGEX.fullmatch(value))

    @classmethod
    def _eq_unit(cls, a: str, b: str) -> bool:
        if (a is None) != (b is None):
            return False
        if a is not None and cls._UR.get_name(a) != cls._UR.get_name(b):
            return False
        return True

    def to(self, new_unit: str) -> 'Quantity':
        """
        Convert to another unit system.
        :param new_unit: The target unit system.
        :return: A new quantity value using the target unit system
        """
        def conv(original: str) -> str:
            """
            Converts a value from current unit to the new_unit
            :param original: string representing a number
            :return: string representing converted number
            """
            # Decimal type is not so well supported in pint package
            # but it preserves precisions and doesn't have numeric errors
            #
            # It fails if the conversion between two units involves an offset
            # e.g. Kelvin -> Celsius
            old = self._UR.Quantity(Decimal(original), self.unit)
            new = old.to(new_unit)
            return str(new.magnitude)

        return Quantity(
            conv(self.value),
            new_unit,
            None if not self.error else (
                conv(self.error[0]),
                conv(self.error[1]),
            ),
            self.is_limit
        )

    def get_error_or_limit(self, is_limit: bool) -> Tuple[str, str]:
        """
        Get the error/limit tuple:
            (errorminus, errorplus), or
            (lowerlimit, upperlimit) from this quantity.
        :param is_limit: return limit tuple? otherwise error tuple
        """
        # conversion not need
        if not (self.error and is_limit != self.is_limit):
            return self.error
        if is_limit:
            # convert to limit/bound tuple
            return (
                str(Decimal(self.value) - Decimal(self.error[0])),
                str(Decimal(self.value) + Decimal(self.error[1]))
            )
        else:
            # convert to error tuple
            return (
                str(Decimal(self.value) - Decimal(self.error[0])),
                str(Decimal(self.error[1]) - Decimal(self.value))
            )

    def can_update_error(self, other: 'Quantity') -> bool:
        """
        Returns whether the error term of this quantity can be updated from
        the other quantity.

        Assumes the two quantities already have the same value and unit,
        otherwise the return value makes no sense.
        :param other: the other quantity
        """
        assert self._eq_unit(self.unit, other.unit)

        # the new quantity has no error term
        if not other.error:
            return False

        # this quantity has no error term, can always update
        if not self.error:
            return True

        # they have the same error term
        if self.error == other.error and self.is_limit == other.is_limit:
            return False

        # Cannot conclude yet, because
        # 1. ('0.0', '0.0') equals to ('0', '0')
        # 2. need conversion between errors and limits/bounds
        othererror = other.error

        if self.is_limit != other.is_limit:
            # conversion between errors and limits
            othererror = other.get_error_or_limit(self.is_limit)

        # compare the errors
        for i in range(2):
            if Decimal(self.error[i]) != Decimal(othererror[i]):
                return True

        return False
