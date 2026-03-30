-- Genre lifecycle: first album year as proxy for band formation
-- Shows how many new bands started releasing in each subgenre per decade
with band_first_album as (
    select
        a.band_id,
        min(a.year) as debut_year
    from {{ ref('stg_albums') }} a
    group by a.band_id
),

band_genre as (
    select
        b.band_id,
        b.primary_subgenre,
        bfa.debut_year
    from {{ ref('stg_bands') }} b
    inner join band_first_album bfa on b.band_id = bfa.band_id
    where b.primary_subgenre is not null and b.primary_subgenre != ''
      and bfa.debut_year >= 1970 and bfa.debut_year <= 2024
)

select
    debut_year,
    primary_subgenre,
    count(*) as new_bands
from band_genre
group by debut_year, primary_subgenre
