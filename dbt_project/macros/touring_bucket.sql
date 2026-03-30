{% macro touring_bucket(concert_count_column) %}
    CASE
        WHEN {{ concert_count_column }} BETWEEN 0 AND 5 THEN '0-5'
        WHEN {{ concert_count_column }} BETWEEN 6 AND 20 THEN '6-20'
        WHEN {{ concert_count_column }} BETWEEN 21 AND 50 THEN '21-50'
        WHEN {{ concert_count_column }} BETWEEN 51 AND 100 THEN '51-100'
        ELSE '100+'
    END
{% endmacro %}
