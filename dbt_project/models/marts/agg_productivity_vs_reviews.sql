-- Does releasing more albums correlate with better or worse reviews?
with band_stats as (
    select
        band_id,
        count(*) as album_count,
        avg(avg_review_pct) as avg_review_score
    from {{ ref('stg_albums') }}
    where review_count > 0
    group by band_id
)

select
    case
        when album_count between 1 and 2 then '1-2 albums'
        when album_count between 3 and 5 then '3-5 albums'
        when album_count between 6 and 10 then '6-10 albums'
        when album_count between 11 and 20 then '11-20 albums'
        else '20+ albums'
    end as productivity_bucket,
    count(*) as band_count,
    round(avg(avg_review_score), 1) as avg_review_score,
    round(approx_quantiles(avg_review_score, 100)[offset(50)], 1) as median_review_score,
    round(avg(album_count), 1) as avg_albums
from band_stats
group by 1
