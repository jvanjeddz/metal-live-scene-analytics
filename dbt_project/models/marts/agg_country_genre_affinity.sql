-- Which countries specialize in which subgenres?
-- Uses location quotient: (country's genre share) / (global genre share)
with country_genre as (
    select
        country,
        primary_subgenre,
        count(*) as band_count
    from {{ ref('stg_bands') }}
    where primary_subgenre is not null and primary_subgenre != ''
      and country is not null and country != ''
    group by country, primary_subgenre
),

country_total as (
    select country, sum(band_count) as total
    from country_genre
    group by country
),

genre_total as (
    select primary_subgenre, sum(band_count) as total
    from country_genre
    group by primary_subgenre
),

global_total as (
    select sum(band_count) as total from country_genre
)

select
    cg.country,
    cg.primary_subgenre,
    cg.band_count,
    ct.total as country_total_bands,
    round(cg.band_count * 100.0 / ct.total, 1) as genre_pct_in_country,
    round(
        (cg.band_count * 1.0 / ct.total) /
        (gt.total * 1.0 / g.total),
        2
    ) as location_quotient
from country_genre cg
inner join country_total ct on cg.country = ct.country
inner join genre_total gt on cg.primary_subgenre = gt.primary_subgenre
cross join global_total g
where ct.total >= 50  -- only countries with meaningful metal scenes
  and cg.band_count >= 3
