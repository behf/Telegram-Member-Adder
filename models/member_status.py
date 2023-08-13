from enum import Enum
from json import JSONEncoder
from typing import Any


class MemberStatus(Enum):
    NOT_PROCESSED = 0
    ADDED_TO_GROUP = 1
    SKIPPED_PRIVACY = 2
    SKIPPED_HAS_LEFT = 3
    SKIPPED_ADDER_RESTRICTED = 4


    