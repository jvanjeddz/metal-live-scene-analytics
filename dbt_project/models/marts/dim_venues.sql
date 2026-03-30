{{ config(cluster_by=["country_code"]) }}

with setlists as (
    select * from {{ ref('stg_setlists') }}
)

select
    venue_id,
    max(venue_name) as venue_name,
    max(city_name) as city_name,
    max(state) as state,
    max(country_code) as country_code,
    max(country_name) as country_name,
    avg(latitude) as latitude,
    avg(longitude) as longitude,
    count(*) as concert_count
from setlists
where venue_id is not null and venue_id != ''
group by venue_id
