Unix: [![Unix Build Status](https://img.shields.io/travis/grandrew/taskjuggler-python/master.svg)](https://travis-ci.org/grandrew/taskjuggler-python) Windows: [![Windows Build Status](https://img.shields.io/appveyor/ci/grandrew/taskjuggler-python/master.svg)](https://ci.appveyor.com/project/grandrew/taskjuggler-python)<br>Metrics: [![Coverage Status](https://img.shields.io/coveralls/grandrew/taskjuggler-python/master.svg)](https://coveralls.io/r/grandrew/taskjuggler-python) [![Scrutinizer Code Quality](https://img.shields.io/scrutinizer/g/grandrew/taskjuggler-python.svg)](https://scrutinizer-ci.com/g/grandrew/taskjuggler-python/?branch=master)<br>Usage: [![PyPI Version](https://img.shields.io/pypi/v/taskjuggler_python.svg)](https://pypi.python.org/pypi/taskjuggler_python)

# Rationale

It's 2017 and still most of the tasks/project management tools lack support for any means of automated planning. This library helps to integrate automated planner that's been available for over a decade, with a shot of suporting different back-ends.

# Overview

Python interfaces to TaskJuggler 3 planner

# Setup

## Requirements

* Python 2.7+
* TaskJuggler 3.6+

## Installation

Install taskjuggler_python with pip:

```sh
$ pip install taskjuggler_python
```

or directly from the source code:

```sh
$ git clone https://github.com/grandrew/taskjuggler-python.git
$ cd taskjuggler-python
$ python setup.py install
```

Install TaskJuggler with gem:

```sh
$ gem install taskjuggler
```

# Usage

After installation, the package can imported:

```sh
$ python
>>> import taskjuggler_python
>>> taskjuggler_python.__version__
```

# TODO

## TaskJuggler support

- working hours, shifts
- priority
- mark tasks as done / decouple depends
- appointments 
    - date+time - `period`
    - date only (as in "do at deadline")
- *deadline (date) - is a check that the task is not scheduled after this date [not in planner - this is a check and can not be enforced]*
- task grouping
- limits dailymax, etc.
- fixed stat time/end time (ALAP/ASAP strats)
    - period for appointments
- non-splittable tasks (`X = effort; limits { maximum Xh }` ??), split punishing
- extensive timezone support

## General enhancements

- Loading scheduling results
    - export back to json
- Make ID management transparent in the API
- Extensive testing including safe strings checks
- TaskJuggler task identifier full path, subtask and validation
- Bookings and timesheets support
- Monte-carlo simulations
- Provide JSONEncoder and JSONDecoder interfaces for jsonjuggler module
    - https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable 
- Data collection, analytics and prediction (e.g. average task error)
    - Store bookings and do automatic progress analytics
- Different backend support (e.g. OptaPlanner/Drools; rename to `python-planner` package?)
    - produce multivariare pareto-optimal solutions
    - export to MiniZinc / FlatZinc for generic CP solvers
    - GPU-accelerated CP solvers?
    - QCL (Quantum Computation Language) export
