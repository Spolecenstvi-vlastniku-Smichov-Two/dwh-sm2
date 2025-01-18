with source as (
    select 'sm2_01' as location, sm2_01.* from {{ ref('sm2_01') }} as sm2_01
    union all
    select 'sm2_02' as location, sm2_02.* from {{ ref('sm2_02') }} as sm2_02
    union all
    select 'sm2_03' as location, sm2_03.* from {{ ref('sm2_03') }} as sm2_03
    union all
    select 'sm2_04' as location, sm2_04.* from {{ ref('sm2_04') }} as sm2_04
    union all
    select 'sm2_05' as location, sm2_05.* from {{ ref('sm2_05') }}as  sm2_05
    union all
    select 'sm2_06' as location, sm2_06.* from {{ ref('sm2_06') }} as sm2_06
    union all
    select 'sm2_07' as location, sm2_07.* from {{ ref('sm2_07') }} as sm2_07
    union all
    select 'sm2_08' as location, sm2_08.* from {{ ref('sm2_08') }} as sm2_08
    union all
    select 'sm2_09' as location, sm2_09.* from {{ ref('sm2_09') }} as sm2_09
),
unpivoted as (
    select Date as time, location, 'temp_ambient' as data_key, venkov as data_value from source
    union all
    select Date as time, location, 'temp_intake' as data_key, sani as data_value from source
    union all
    select Date as time, location, 'temp_indoor' as data_key, odvod as data_value from source
    union all
    select Date as time, location, 'temp_fresh' as data_key, privod as data_value from source
    union all
    select Date as time, location, 'temp_waste' as data_key, vyfuk as data_value from source
),
final as (
    select 
        strptime(time, '%d.%m.%Y %H:%M:%S') as time, 
        location, 
        data_key, 
        cast(replace(data_value,',','.') as decimal) as data_value 
    from unpivoted
    union
    {{ sources('csv_google','fact') }}
)

select * from final
