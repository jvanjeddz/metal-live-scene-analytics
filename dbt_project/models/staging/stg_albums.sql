with source as (
    select * from {{ source('raw', 'albums') }}
),

parsed as (
    select
        band_id,
        album_name,
        album_type,
        safe_cast(year as int64) as year,
        {{ parse_review_count('reviews') }} as review_count,
        {{ parse_review_pct('reviews') }} as avg_review_pct
    from source
),

deduped as (
    select
        *,
        row_number() over (
            partition by band_id, album_name, year
            order by review_count desc
        ) as rn
    from parsed
    where year is not null
)

select
    to_hex(md5(band_id || '|' || album_name || '|' || cast(year as string))) as album_id,
    band_id,
    album_name,
    album_type,
    year,
    review_count,
    avg_review_pct
from deduped
where rn = 1
