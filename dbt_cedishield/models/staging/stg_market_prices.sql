select
    market_date as timestamp,
    ticker,
    open_price as open,
    high_price as high,
    low_price as low,
    close_price as close,
    volume
from {{ source('cedishield_bronze', 'bronze_market_prices') }}