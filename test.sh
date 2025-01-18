#!/bin/bash
#
# Script to split a string based on the delimiter

my_string="Date;KOT1/Teplota venkovní (°C);KOT1/VZT 01 | Obj. 1/vzt01_temp-tea-sani (°C);KOT1/VZT 01 | Obj. 1/vzt01_temp-teb-odvod (°C);KOT1/VZT 01 | Obj. 1/vzt01_temp-tu1-privod (°C);KOT1/VZT 01 | Obj. 1/vzt01_temp-tu2-vyfuk (°C);"
IFS=';' read -ra my_array <<< "$my_string"

#Print the split string
for i in "${my_array[@]}"
do
  for Item in 'Date' 'venkov' 'sani' 'odvod' 'privod' 'vyfuk' ;  
  do
    if [[ $i == *"$Item"* ]]; then
      echo "$Item"
    fi
  done
done
