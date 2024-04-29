# M/M/1 Queue Implementation and Analysis in Python

## About

This repository contains an implementation of a M/M/1 queue with an inter-arrival rate of 3 units per hour and a service rate of 4 units per hour. The simulation runs for 500 hours and outputs the following parameters:

- The average length of the queue
- The average length of the system
- The average wait time in the queue
- The average wait time in the system
- The average utilization of the single server.

Additionally, the code replications the queue simulation for 30, 100, and 1000 replications and utilizes hypothesis testing to compare the output parameters to the expected theoretical parameters and the resulting parameters from an equivalent AnyLogic queue simulation.

## Setup

To setup the repository the environment for the `main.py` script, ensure that the Python interpreter is installed and run the following in a bash shell after navigating to the cloned repository directory.

``` bash
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

## Usage

To utilize the `main.py` script, ensure the `venv` is sourced and the requirements are installed (see Setup above). Then, the following usage string may be utilized.

``` txt
Usage: main.py -f output_spreadsheet_path -r replications
```

Both the `-f` and `-r` must be provided, although the order in which they appear does not matter. Example practical usages are the following.

``` bash
$ python3 main.py -f repl30.xlsx -r 30
$ python3 main.py -r 100 -f repl100.xlsx
```
