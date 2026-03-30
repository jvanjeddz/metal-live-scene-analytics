-- Review score distribution per subgenre for box/violin plots
with album_reviews as (
    select
        b.primary_subgenre,
        a.avg_review_pct
    from {{ ref('stg_albums') }} a
    inner join {{ ref('stg_bands') }} b on a.band_id = b.band_id
    where a.review_count > 0
      and a.avg_review_pct is not null
      and b.primary_subgenre is not null
      and b.primary_subgenre != ''
),

genre_counts as (
    select primary_subgenre, count(*) as n
    from album_reviews
    group by primary_subgenre
)

select
    ar.primary_subgenre,
    ar.avg_review_pct
from album_reviews ar
inner join genre_counts gc on ar.primary_subgenre = gc.primary_subgenre
where gc.n >= 50
