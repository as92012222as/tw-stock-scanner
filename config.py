# config.py

import datetime

# --- System Configuration ---
# Set timezone to Taiwan (UTC+8)
TZ_TAIWAN = datetime.timezone(datetime.timedelta(hours=8))

# Data Fetching Delays (in seconds)
# To avoid being blocked by Yahoo Finance / twstock
API_DELAY_SECONDS = 1.2

# --- Strategy Constants ---
# Lookback period for fetching data (in days)
DATA_LOOKBACK_DAYS = 100

# Moving Average periods
MA_SHORT = 5
MA_MID = 10
MA_LONG = 20

# Minimum Volume Threshold (in shares, e.g., 1000000 shares = 1000 lots)
MIN_VOLUME_THRESHOLD = 1000000

# Consecutive invalid date count to stop scanning (detecting holiday/non-trading day)
HOLIDAY_DETECT_THRESHOLD = 10

# --- File Paths ---
RESULT_CSV_FILE = 'result.csv'
