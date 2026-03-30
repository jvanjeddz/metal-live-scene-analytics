with yearly as (
    select
        event_year,
        primary_subgenre,
        count(*) as concert_count
    from {{ ref('fct_concerts') }}
    where primary_subgenre is not null and primary_subgenre != ''
    group by event_year, primary_subgenre
),

yearly_total as (
    select
        event_year,
        sum(concert_count) as total
    from yearly
    group by event_year
)

select
    y.event_year,
    y.primary_subgenre,
    y.concert_count,
    round(y.concert_count * 100.0 / yt.total, 1) as concert_share_pct
from yearly y
inner join yearly_total yt on y.event_year = yt.event_year
