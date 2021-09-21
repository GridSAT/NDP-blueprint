# NasserSatSolver-Python

### Installation

##### Prepare system virtualenv

On ubuntu run as root

```bash
apt install python3-pip libpq-dev
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
