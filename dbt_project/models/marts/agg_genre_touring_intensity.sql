select
    primary_subgenre,
    count(distinct ma_band_id) as band_count,
    count(*) as total_concerts,
    round(count(*) * 1.0 / count(distinct ma_band_id), 1) as avg_concerts_per_band
from {{ ref('fct_concerts') }}
where primary_subgenre is not null and primary_subgenre != ''
group by primary_subgenre
