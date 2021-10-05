import functools
import re
import warnings
import time
from string import ascii_uppercase
from typing import Optional
from dataclasses import dataclass

from googleapiclient.errors import HttpError

MAX_RETRY_ATTRIBUTE = "max_retry"
SLEEP_ATTRIBUTE = "sleep"


def retry_on_out_of_quota():
    """A decorator to give wrapped function ability to retry on quota exceeded related HttpError raise by Google API.
    It only works on class method and requires "max_retry" and "sleep" attribute in the class. If `max_retry` is
    non-positive, no retry will be attempt. `sleep` is the base number of seconds between consecutive retries. The number
    of wait seconds will double after each sleep.

    :return:
    """
    def wrapper(method):
        @functools.wraps(wrapped=method)
        def wrapped_function(self, *args, **kwargs):
            max_retry = getattr(self, MAX_RETRY_ATTRIBUTE, 0)
            max_retry = max(max_retry, 0)
            sleep = getattr(self, SLEEP_ATTRIBUTE, 5)
            if sleep < 0:
                raise AttributeError(f"{SLEEP_ATTRIBUTE} must be positive. Got {sleep}")

            pattern = re.compile(".*(User Rate Limit Exceeded|Quota exceeded)+.*")
            while True:
                max_retry -= 1
                try:
                    result = method(self, *args, **kwargs)
                    return result
                except HttpError as e:
                    if max_retry >= 0 and pattern.match(str(e)):
                        warnings.warn(f"handled exception {e}. remaining retry: {max_retry}", UserWarning)
                        time.sleep(sleep)
                        sleep = sleep*2
                        continue

                    raise e

        return wrapped_function

    return wrapper


@dataclass(frozen=True)
class Shape:
    from_col: int
    from_row: int
    to_col: int
    to_row: Optional[int]

    def __repr__(self):
        end_row = "" if self.to_row is None else str(self.to_row)

        return f"{get_col_from_number(self.from_col)}{self.from_row}:{get_col_from_number(self.to_col)}{end_row}"

    @property
    def size(self):
        col_num = self.to_col - self.from_col + 1
        row_num = None if self.to_row is None else self.to_row - self.from_row + 1
        return (row_num, col_num)

    def can_contain(self, shape: tuple) -> bool:
        """Check if the size of this shape is big enough for another rectangle defined by the given shape.

        :param shape: a tuple of row count and col count.
        :return: Whether the size of this shape is big enough.
        """
        if self.size[0] < shape[0]:
            return False

        return self.size[1] is None or self.size[1] >= shape[1]


class Range:
    _pattern = re.compile("^([A-Z]*)([0-9]+)$", re.IGNORECASE)

    def __init__(self, a1_notation: str):
        self._range = a1_notation
        self._sheet, self._cells = self._get_sheet_and_cells()
        self._shape = self._get_shape()

    def __str__(self):
        return self._range

    def __repr__(self):
        return self._range

    @property
    def range(self):
        return self._range

    @property
    def shape(self):
        return self._shape

    @property
    def size(self):
        return self._shape.size

    @property
    def sheet(self):
        return self._sheet

    @property
    def cells(self):
        return self._cells

    def can_contain(self, target: tuple) -> bool:
        return self._shape.can_contain(target)

    def _get_sheet_and_cells(self):
        _sheet, _cells = self._range.split("!")
        return _sheet.upper(), _cells.upper()

    def _get_shape(self) -> Shape:
        try:
            _from, _to = self._cells.split(":")
        except:
            raise ValueError(f"Invalid range {self._sheet}:{self._range}")

        _from_col, _from_row = self._get_col_and_row(_from)
        _to_col, _to_row = self._get_col_and_row(_to)
        return Shape(get_column_number(_from_col), int(_from_row), get_column_number(_to_col), int(_to_row))

    def _get_col_and_row(self, cell: str):
        if self._pattern.match(cell) is None:
            raise ValueError(f"Invalid cell {cell}")

        return self._pattern.search(cell).groups()


def get_column_number(col: str) -> int:
    """Convert spreadsheet column numbers to integer.

    :example:

    >>> get_column_number('A')  # 1
    >>> get_column_number('AA') # 27
    >>> get_column_number('ZY') # 701

    :param col: upper case spreadsheet column
    :return: index of the column starting from 1.
    """
    result = 0
    l = len(col)
    for i in range(l):
        result += (ord(col[l-i-1]) - 64) * (26 ** i)

    return result


def get_col_from_number(col_idx: int) -> str:
    """Convert column value from index. This is the reverse of get_column_number

    :param col_idx: a positive integer representing column number
    :return: alphabetical col name used in A1 notation
    """
    col = ""
    while col_idx > 0:
        col_idx -= 1
        remainder = col_idx % 26
        col_idx = col_idx // 26
        col = ascii_uppercase[remainder] + col
    return col


def get_col_counts_from_range(sheet_range: str) -> int:
    """Calculate the number of columns in the given range.

    :example:

    >>> get_col_counts_from_range("test!A1:A")  # 1
    >>> get_col_counts_from_range("test!A1:D")  # 4
    >>> get_col_counts_from_range("test!AA2:AZ")  # 26

    :param sheet_range: a string representation of sheet range. For example, "test_sheet!A1:D"
    :return: the number of columns contained in the range.
    """
    columns = sheet_range.upper().split("!")[1]  # get the columns in letter, such as "A1:D"
    from_column, to_column = columns.split(":")
    pattern = re.compile("^([A-Z]+)", re.IGNORECASE)
    from_column = pattern.search(from_column).group(0)
    to_column = pattern.search(to_column).group(0)
    counts = get_column_number(to_column) - get_column_number(from_column) + 1
    return counts
