-- Monthly distribution of concerts to reveal festival season patterns
select
    event_month,
    case event_month
        when 1 then 'Jan' when 2 then 'Feb' when 3 then 'Mar'
        when 4 then 'Apr' when 5 then 'May' when 6 then 'Jun'
        when 7 then 'Jul' when 8 then 'Aug' when 9 then 'Sep'
        when 10 then 'Oct' when 11 then 'Nov' when 12 then 'Dec'
    end as month_name,
    count(*) as concert_count,
    count(distinct ma_band_id) as unique_bands,
    count(distinct country_code) as unique_countries
from {{ ref('fct_concerts') }}
group by event_month
