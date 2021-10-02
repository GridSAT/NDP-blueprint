#!/bin/bash

# arg 1 = head | node to start ray
if [[ "$1" != "head" && "$1" != "node" ]]
then
  echo "Please call "$(basename $0)" with `head` or `node` to start the service!"
  exit 1
fi

if [[ "$2" != "" ]]
then
  ADDRESS=$2
else
  ADDRESS=$(hostname)
fi

if [[ "$3" != "" ]]
then
  CPUS=$3
else
  CPUS=$(( $(lscpu --online --parse=CPU | egrep -v '^#' | wc -l) - 4 ))
fi

ray-start.sh $1 $ADDRESS $CPUS | grep 'Ray runtime started.'

echo "Running until Ctrl-C"

bash -c "sysinfo.sh $CPUS"

echo ""

ray-stop.sh

echo ""
