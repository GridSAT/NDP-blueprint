<!--
#	README.md
#
#	Non-Deterministic Processor (NDP) blueprint
#	Copyright (c) 2022 GridSAT Stiftung
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.

#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see <https://www.gnu.org/licenses/>.

#	GridSAT Stiftung - Georgstr. 11 - 30159 Hannover - Germany - info@gridsat.io
#
-->


# Non-Deterministic Processor (NDP) blueprint

### Installation

##### Prepare system virtualenv

On ubuntu run as root

```bash
apt install python3-pip libpq-dev sysstat
```

##### Create virtualenv

Log-in as user and run

```bash
cd /path/pattern_solvers

virtualenv pattern_solvers
```


### Activate and update virtualenv

Login as user and run

```bash
cd /path/pattern_solvers

source pattern_solvers/bin/activate

pip install -r requirements
```


### Startup the RAY nodes to allow multi-processing on cluster

Using [ray](https://docs.ray.io) for upscaling the showcase.

The installation is already done after pip install from previous steps

##### Start the head node

```bash
export RAY_DISABLE_IMPORT_WARNING=1
CPUS=$(( $(lscpu --online --parse=CPU | egrep -v '^#' | wc -l) - 4 ))
ray start --head --include-dashboard=false --num-gpus=0 --num-cpus=$CPUS
```

##### Start the additional nodes

```bash
export RAY_DISABLE_IMPORT_WARNING=1
CPUS=$(( $(lscpu --online --parse=CPU | egrep -v '^#' | wc -l) - 4 ))
ray start --include-dashboard=false --address='MASTER-IP:6379' --redis-password='MASTER-PASSWORT' --num-gpus=0 --num-cpus=$CPUS
```

To add more worker nodes just run same on additional nodes



### Run solver

```bash
python3 main.py -v -d inputs/Multi11bit.txt -m lou -t 8
```

The solver main process will connect automatically to the head node and use the workers as given.



### Starter tools

Some helpers to easily run the processes and environments.

```bash

# .bin/ray.sh
sudo su - easyxps

# .bin/ray-auto.sh
sudo -u easyxps -i /bin/bash -i -c ray-auto.sh

# .bin/node.sh
ssh -i $HOME/.ssh/AWS.pem "node$1"

# .bin/node-up.sh
ssh -i $HOME/.ssh/AWS.pem "node$1" -t .bin/ray-auto.sh

# run and log unbuffered (need expect-dev installed)
CORES="0001"; BITS="14"; ( echo "START: `date`"; echo ""; unbuffer python3 main.py -v -d inputs/Multi"$BITS"bit.txt -m lou -t $CORES 2>/dev/null ; echo "" ; echo "ENDE: `date`" ) | tee logs/$(date "+%Y-%m-%d")_Multi"$BITS"bit-$CORES-Cores.txt

# run and start on Node1
cd $HOME/Workspace/off-limits; source __venv__/bin/activate ; PATH=$PATH:/home/xps/Workspace/off-limits/bin ray-auto.sh head node1 8

# run and start on a Node
cd $HOME/Workspace/off-limits; source __venv__/bin/activate ; PATH=$PATH:/home/xps/Workspace/off-limits/bin ray-auto.sh node node1 22

```
