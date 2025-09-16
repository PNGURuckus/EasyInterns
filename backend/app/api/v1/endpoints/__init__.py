# This file makes the endpoints directory a Python package

# Import all endpoint modules
from . import auth
from . import internships
from . import ranking

# List of all available endpoint modules
__all__ = [
    "auth",
    "internships",
    "ranking",
]
