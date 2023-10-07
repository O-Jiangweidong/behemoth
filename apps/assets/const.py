from enum import Enum
from gettext import gettext as _


class PlatformCategory(str, Enum):
    mysql = 'mysql'
    publisher = 'publisher'

