with source as ( --noqa
    select cast(columns(*) as varchar) from {{ source('csv_google','merged') }}
),

unpivoted as (
    unpivot source --noqa
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

params as (
    select
        date_trunc(
            'month', now()) - interval (b.history - 1
            ) month as start_ts
    from {{ ref('mapping_sources') }} as b
    where b.file_nm = 'fact.csv'
),

final as (
    select
        cast(time as timestamp) as time, 
        location,
        data_key,
        data_value
    from mapped
    union distinct
    select * from {{ source('csv_google','fact_original') }}
)

select *
from final
where time >= (select max(start_ts) from params)
