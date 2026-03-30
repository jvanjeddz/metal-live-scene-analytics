with source as (
    select * from {{ source('raw', 'bands') }}
),

deduped as (
    select
        *,
        row_number() over (partition by band_id order by band_name) as rn
    from source
)

select
    band_id,
    band_name,
    country,
    genre,
    {{ parse_subgenre('genre') }} as primary_subgenre,
    status
from deduped
where rn = 1
