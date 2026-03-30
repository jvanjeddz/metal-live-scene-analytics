select
    event_year,
    event_month,
    count(*) as concert_count
from {{ ref('fct_concerts') }}
group by event_year, event_month
