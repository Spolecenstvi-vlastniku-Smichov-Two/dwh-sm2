with source as (
    select cast(columns(*) as varchar) from {{ source('csv_google','merged') }}
),

unpivoted as (
    unpivot source
    on columns(* exclude (date))
    into
    name data_key_original
    value data_value
),

mapped as (
    select
        unpivoted.date as "time", --noqa
        mapping.location,
        mapping.data_key,
        unpivoted.data_value
    from unpivoted
    inner join {{ ref('mapping') }} as mapping --noqa
        on unpivoted.data_key_original = mapping.data_key_original
    where unpivoted.date is not null
),

final as (
    select
        time, --strptime(time, '%d.%m.%Y %H:%M:%S') as time, 
        location,
        data_key,
        data_value
    from mapped
    union distinct
    select * from {{ source('csv_google','fact_original') }}
)

select * from final
