with source as (
    select * from {{ source('raw', 'band_mapping') }}
)

select
    cast(ma_band_id as string) as ma_band_id,
    ma_band_name,
    sfm_mbid,
    sfm_artist_name,
    match_type
from source
