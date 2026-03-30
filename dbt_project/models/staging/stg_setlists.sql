with source as (
    select * from {{ source('raw', 'setlists') }}
),

deduped as (
    select
        *,
        row_number() over (partition by setlist_id order by event_date) as rn
    from source
)

select
    setlist_id,
    artist_mbid,
    artist_name,
    event_date,
    extract(year from event_date) as event_year,
    extract(month from event_date) as event_month,
    venue_id,
    venue_name,
    city_name,
    state,
    country_code,
    country_name,
    cast(latitude as float64) as latitude,
    cast(longitude as float64) as longitude,
    tour_name
from deduped
where rn = 1
