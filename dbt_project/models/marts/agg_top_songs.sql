with songs as (
    select * from {{ ref('stg_songs') }}
),

setlists as (
    select * from {{ ref('stg_setlists') }}
)

select
    sg.song_name,
    s.artist_name,
    count(*) as performance_count,
    count(distinct s.venue_id) as unique_venue_count
from songs sg
inner join setlists s on sg.setlist_id = s.setlist_id
where sg.song_name is not null and sg.song_name != ''
group by sg.song_name, s.artist_name
