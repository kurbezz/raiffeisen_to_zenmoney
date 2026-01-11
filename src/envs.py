"""Legacy environment configuration module.

This module maintains backward compatibility by loading configuration
from the YAML config file using the config reader.
"""

from config import get_config

# Load configuration from YAML
_config = get_config()

# Email configuration
EMAIL_USERNAME = _config.email_username
EMAIL_PASSWORD = _config.email_password
EMAIL_ALLOWED_SUBJECTS = _config.email_allowed_subjects

# Zen Money configuration
ZEN_MONEY_API_KEY = _config.zen_money_api_key
USER_ID = _config.zen_money_user_id

# Currency configuration
CURRENCY_CONFIG = _config.currency_config

# Category configuration
CATEGORY_CONFIG = _config.category_config

# Deel configuration
DEEL_CONFIG = _config.deel_config

# Cash withdrawal configuration
CASH_WITHDRAWAL_CONFIG = _config.cash_withdrawal_config
