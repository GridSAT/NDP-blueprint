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
  if [[ "$OSTYPE" == "darwin"* ]]
  then
    CPUS=$(( sysctl -a | grep 'cpu.thread_count' | sed -e 's/[^0-9]//g' ))
  else
    CPUS=$(( $(lscpu --online --parse=CPU | egrep -v '^#' | wc -l) - 4 ))
  fi
fi

export RAY_DISABLE_IMPORT_WARNING=1

if [[ "$1" == "head" ]]
then
  ray start --head --include-dashboard=false --num-gpus=0 --num-cpus=$CPUS
else
  ray start        --include-dashboard=false --address="$ADDRESS:6379" --redis-password='5241590000000000' --num-gpus=0 --num-cpus=$CPUS
fi
