{% macro parse_subgenre(genre_column) %}
    trim(
        regexp_extract(
            regexp_extract({{ genre_column }}, r'^([^(]+)'),
            r'^([^/,]+)'
        )
    )
{% endmacro %}
