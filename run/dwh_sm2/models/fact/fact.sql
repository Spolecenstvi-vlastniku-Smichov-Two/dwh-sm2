
    create or replace view "dwh_sm2"."main"."fact__dbt_int" as (
      select * from read_csv('./fact.csv', auto_detect=True)
    );
    