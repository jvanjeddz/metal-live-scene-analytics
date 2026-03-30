{% macro parse_review_count(reviews_column) %}
    CASE
        WHEN {{ reviews_column }} IS NULL OR {{ reviews_column }} = 'No Reviews' THEN 0
        ELSE CAST(regexp_extract({{ reviews_column }}, r'^(\d+)') AS INT64)
    END
{% endmacro %}

{% macro parse_review_pct(reviews_column) %}
    CASE
        WHEN {{ reviews_column }} IS NULL OR {{ reviews_column }} = 'No Reviews' THEN NULL
        ELSE CAST(regexp_extract({{ reviews_column }}, r'\((\d+)%\)') AS INT64)
    END
{% endmacro %}
