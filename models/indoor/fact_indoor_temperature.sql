with source as (
    select * from {{ source('csv_google_indoor','merged_indoor') }}
),

mapped as (
    select
        source.Datetime as "time", --noqa
        mapping.location,
        'temp_indoor' as data_key,
        source.Temperature_Celsius as data_value
    from source
    inner join {{ ref('mapping_indoor') }} as mapping --noqa
        on source.location = mapping.sensor
    where source.Datetime is not null
),

final as (
    select
        time, 
        location,
        data_key,
        data_value
    from mapped
    union distinct
    select * from {{ source('csv_google_indoor','fact_indoor_temperature_original') }}
)

select * from final
