select
    accession_number,
    entity_name,
    fiscal_year,
    start_date,
    filed_date,
    value
from {{ source('cedishield_bronze', 'bronze_sec_facts') }}