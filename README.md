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


### Run solver

```bash
python3 main.py -v -d inputs/Multi11bit.txt -m lou -t 8
```
