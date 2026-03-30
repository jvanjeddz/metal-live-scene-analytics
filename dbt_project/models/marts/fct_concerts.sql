{{
    config(
        materialized='table',
        partition_by={
            "field": "event_date",
            "data_type": "date",
            "granularity": "month"
        },
        cluster_by=["primary_subgenre", "country_code"]
    )
}}

with setlists as (
    select * from {{ ref('stg_setlists') }}
),

mapping as (
    select * from {{ ref('stg_band_mapping') }}
),

bands as (
    select * from {{ ref('stg_bands') }}
),

songs_agg as (
    select
        setlist_id,
        count(*) as song_count
    from {{ ref('stg_songs') }}
    group by 1
),

album_stats as (
    select
        band_id,
        avg(avg_review_pct) as avg_review_score,
        sum(review_count) as review_count
    from {{ ref('stg_albums') }}
    where review_count > 0
    group by 1
)

select
    s.setlist_id as concert_id,
    b.band_id as ma_band_id,
    s.artist_name,
    b.primary_subgenre,
    s.event_date,
    s.event_year,
    s.event_month,
    s.venue_name,
    s.city_name,
    s.country_code,
    s.country_name,
    s.latitude,
    s.longitude,
    s.tour_name,
    coalesce(sa.song_count, 0) as song_count,
    ar.avg_review_score,
    ar.review_count
from setlists s
inner join mapping m on s.artist_mbid = m.sfm_mbid
inner join bands b on m.ma_band_id = b.band_id
left join songs_agg sa on s.setlist_id = sa.setlist_id
left join album_stats ar on b.band_id = ar.band_id
