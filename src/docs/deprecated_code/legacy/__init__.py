"""
Legacy file-based transformation functions.
Maintained for backward compatibility.

Note: The file-based approach is deprecated and will be removed in a future version.
Please transition to the object-based pipeline API.
"""

import logging
import warnings
from ... import config

logger = logging.getLogger(__name__)

# Show deprecation warning when this module is imported
config.show_file_mode_deprecation_warning(logger)