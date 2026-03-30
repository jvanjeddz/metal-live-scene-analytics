{{ config(cluster_by=["country", "primary_subgenre"]) }}

with bands as (
    select * from {{ ref('stg_bands') }}
),

mapping as (
    select * from {{ ref('stg_band_mapping') }}
),

album_stats as (
    select
        band_id,
        count(*) as total_albums,
        avg(avg_review_pct) as avg_review_score,
        sum(review_count) as total_reviews
    from {{ ref('stg_albums') }}
    group by 1
),

concert_stats as (
    select
        ma_band_id,
        count(*) as total_concerts
    from {{ ref('fct_concerts') }}
    group by 1
)

select
    b.band_id as ma_band_id,
    b.band_name,
    b.country,
    b.primary_subgenre,
    b.genre as full_genre,
    b.status,
    m.sfm_mbid,
    m.sfm_mbid is not null as has_setlist_data,
    coalesce(a.total_albums, 0) as total_albums,
    a.avg_review_score,
    coalesce(a.total_reviews, 0) as total_reviews,
    coalesce(c.total_concerts, 0) as total_concerts
from bands b
left join mapping m on b.band_id = m.ma_band_id
left join album_stats a on b.band_id = a.band_id
left join concert_stats c on b.band_id = c.ma_band_id
