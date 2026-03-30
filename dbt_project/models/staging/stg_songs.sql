with source as (
    select * from {{ source('raw', 'songs') }}
),

deduped as (
    select
        *,
        row_number() over (
            partition by setlist_id, song_name, set_name
            order by song_name
        ) as rn
    from source
)

select
    to_hex(md5(setlist_id || '|' || song_name || '|' || coalesce(set_name, '') || '|' || cast(encore as string))) as song_id,
    setlist_id,
    song_name,
    set_name,
    cast(encore as int64) as encore,
    coalesce(is_cover, false) as is_cover,
    cover_artist_name,
    coalesce(is_tape, false) as is_tape
from deduped
where rn = 1
  and (is_tape is null or is_tape = false)
  and song_name is not null
  and song_name != ''
