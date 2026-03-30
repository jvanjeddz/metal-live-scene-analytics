with source as (
    select * from {{ source('raw', 'labels') }}
)

select
    label_id,
    band_id,
    label_name,
    specialization,
    status,
    country
from source
where label_id is not null and label_id != ''
