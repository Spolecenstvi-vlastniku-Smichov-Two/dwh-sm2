select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select time
from "dwh_sm2"."main"."fact"
where time is null



      
    ) dbt_internal_test