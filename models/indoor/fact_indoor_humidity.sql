with source as (
    select * from {{ source('csv_google_indoor','merged_indoor') }}
),

mapped as (
    select
        source.Datetime as "time", --noqa
        mapping.location,
        'humidity_indoor' as data_key,
        source."Relative_Humidity(%)" as data_value --noqa
    from source
    inner join {{ ref('mapping_indoor') }} as mapping --noqa
        on source.location = mapping.sensor
    where source.datetime is not null
),

params as (
    select
        date_trunc(
            'month', now()) - interval (b.history - 1
            ) month as start_ts
    from {{ ref('mapping_sources') }} as b
    where b.file_nm = 'fact_indoor_humidity.csv'
),

final as (
    select
        time,
        location,
        data_key,
        data_value
    from mapped
    union distinct
    select *
    from {{ source('csv_google_indoor','fact_indoor_humidity_original') }}
)

select *
from final
where time >= (select max(start_ts) from params)
