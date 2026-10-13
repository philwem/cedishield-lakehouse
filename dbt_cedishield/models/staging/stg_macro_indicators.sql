select
    country_code,
    indicator_id as indicator_code,
    indicator_name,
    year,
    value
from {{ source('cedishield_bronze', 'bronze_macro_indicators') }}