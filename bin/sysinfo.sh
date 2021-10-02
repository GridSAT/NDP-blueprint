#!/bin/bash

# Regular Colors
Black='\033[0;30m'        # Black
Red='\033[1;31m'          # Red
Green='\033[0;32m'        # Green
Yellow='\033[1;33m'       # Yellow
Blue='\033[0;34m'         # Blue
Purple='\033[1;35m'       # Purple
Cyan='\033[0;36m'         # Cyan
White='\033[0;37m'        # White

CPUS=$(lscpu --online --parse=CPU | egrep -v '^#' | wc -l)
if [[ "$1" != "" ]]
then
	CPUSUSED=$1
else
	CPUSUSED=$(( $CPUS - 4 ))
fi

trap exit SIGINT

while [[ 1 == 1 ]]
do
	DATE=$(date)
	HOSTIP=$(hostname)
	LOAD=$(grep 'cpu ' /proc/stat | awk '{printf("%6.1f"), ($2+$4)*100/($2+$4+$5)}')
	LOAD=$(mpstat 1 1 | tail -n 1 | awk '$12 ~ /[0-9.]+/ { printf("%6.1f"), 100 - $12 }')
	MEMUSED=$(free -t | awk 'FNR == 2 {printf("%6.1f"), $3/$2*100}')
	PROCESSES=$(ps -e -f | cut -d ' ' -f 1 | grep -i xps | wc -l)

	VALUE=$(printf "%.0f" $LOAD)
	if (( $VALUE <= 30 ))
	then
		LOADCOL=$Green
	else
		LOADCOL=$Red
	fi

	VALUE=$(printf "%.0f" $MEMUSED)
	if (( $VALUE <= 50 ))
	then
		MEMUSEDCOL=$Green
	else
		MEMUSEDCOL=$Purple
	fi

	VALUE=$(printf "%.0f" $PROCESSES)
	if (( $VALUE <= 25 ))
	then
		PROCCOL=$Green
	else
		PROCCOL=$Yellow
	fi

	echo -e "    $HOSTIP | $DATE | CPUS: $CPUSUSED/$CPUS | LOAD: ${LOADCOL}${LOAD}%${White} | MEM: ${MEMUSEDCOL}${MEMUSED}%${White} | PROCESSES: ${PROCCOL}${PROCESSES}${White}          \r\c"
	sleep 0.25
done
