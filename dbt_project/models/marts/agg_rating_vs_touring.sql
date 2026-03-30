with band_concerts as (
    select
        ma_band_id,
        count(*) as total_concerts,
        avg(avg_review_score) as avg_review_score
    from {{ ref('fct_concerts') }}
    where avg_review_score is not null
    group by ma_band_id
)

select
    {{ touring_bucket('total_concerts') }} as touring_bucket,
    count(*) as band_count,
    round(avg(avg_review_score), 1) as avg_review_score,
    round(approx_quantiles(avg_review_score, 100)[offset(50)], 1) as median_review_score
from band_concerts
group by 1
