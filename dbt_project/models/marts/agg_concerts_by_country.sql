select
    country_code,
    country_name,
    count(*) as concert_count,
    avg(latitude) as avg_latitude,
    avg(longitude) as avg_longitude
from {{ ref('fct_concerts') }}
where country_code is not null and country_code != ''
group by country_code, country_name
