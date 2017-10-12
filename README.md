Unix: [![Unix Build Status](https://img.shields.io/travis/grandrew/taskjuggler-python/master.svg)](https://travis-ci.org/grandrew/taskjuggler-python) Windows: [![Windows Build Status](https://img.shields.io/appveyor/ci/grandrew/taskjuggler-python/master.svg)](https://ci.appveyor.com/project/grandrew/taskjuggler-python)<br>Metrics: [![Coverage Status](https://img.shields.io/coveralls/grandrew/taskjuggler-python/master.svg)](https://coveralls.io/r/grandrew/taskjuggler-python) [![Scrutinizer Code Quality](https://img.shields.io/scrutinizer/g/grandrew/taskjuggler-python.svg)](https://scrutinizer-ci.com/g/grandrew/taskjuggler-python/?branch=master)<br>Usage: [![PyPI Version](https://img.shields.io/pypi/v/taskjuggler_python.svg)](https://pypi.python.org/pypi/taskjuggler_python)

# Rationale

It's [whatever current year] and still most of the tasks/project management tools lack support for any means of automated planning. This library helps to integrate automated planner that's been available for over a decade, with a shot of suporting different back-ends.

Life is dynamic and ever-changing. While there is no need to strictly follow the plans, a dynamically recalculating schedule will definitely help to keep up with the pace :-)

- Current focus is on personal planning and small teams (hence no support for multiple resource yet)
- Zero-configuration is required to start

# Overview

`python_taskjuggler` module provides python interfaces to TaskJuggler 3 planner. It is a set of base classes that provide the objects that TaskJuggler internally uses. The module comes with example implementation of JSON project description parser.

It is still work in progress and currently supports:

- generating taskjuggler project file
- runnig the planner
- importing task bookings
- working with single default resource `"me"`

The package comes with an example command line utility `tjp-client` that provides automatic planning for
tasks defined as records in [airtable](https://airtable.com) table. 
Working with google sheets, jira, trello, todoist, smartsheet and others could be implemented the same way.

The utility allows to immediately re-schedule to reflect any changes to the plans that may arise due to new fixed appointments, dependencies, priority amendments or required efforts re-evaluation.

## Command-line utility usage:

### Overview

```
$ tjp-client -a airtable -k <airtable_api_key> -b <airtable_database> -t <table_name> -v <view_name>
```

### Preparation

1. Create an [airtable](https://airtable.com) table with the following fields (case sensitive): 

 ```
    1. id
    2. summary
    3. effort
    4. priority
    5. depends
    6. booking 
```
2. Get `API key`, `database ID`, note your `table name` and `view name`
3. Execute in terminal:

```sh
$ tjp-client -a airtable -k keyAnIuVcuhhkeAkc -b appA8ZtLosVV7HGXy -t Tasks -v Work
```

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

Basic usage concepts include:

1. A `Task`, referred to as `issue` throughout the code
    1. Task's `id` which is used to identify and map the tasks - a property of `JugglerTask` instance
    2. Task's `effort` measured in units set as `UNIT` class attribute of `JugglerTaskEffort`
    3. Task's dependencies
    4. Task's `start` date (a.k.a. fixed appointment)
    5. Task's `priority` measured as interger `0-1000` to set scheduling preference. No priority is scheduled always first.
2. Bookings - the taskjuggler execution result written as `JugglerTask`'s property object(s)

The minimal invocation will look like:

```python
from taskjuggler_python import JsonJuggler
jg = GenericJuggler()
t = juggler.JugglerTask()
jg.add_task(t)
jg.run()
```

## JSON tasks loading:

```sh
$ python
>>> from taskjuggler_python import JsonJuggler
>>> my_tasks = """[
  {
    "id": 2,
    "depends": [
      1
    ],
    "allocate": "me",
    "effort": 1.2
  },
  {
    "id": 1,
    "effort": 3,
    "allocate": "me",
    "summary": "test"
  }
]"""
>>> jg = JsonJuggler(my_tasks)
>>> jg.run()
>>> jg.toJSON()
[
    {
        "allocate": "me",
        "booking": "2017-10-10T11:00:00+00:00",
        "depends": [
            1
        ],
        "effort": 1.2,
        "id": 2
    },
    {
        "allocate": "me",
        "booking": "2017-10-10T08:00:00+00:00",
        "effort": 3,
        "id": 1,
        "summary": "test"
    }
]
```

## Python interface usage example

As an example, let's create interface to automatically schedule tasks that are defined as airtable records
using [Airtable API wrapper](https://github.com/gtalarico/airtable-python-wrapper):

We are using the fact that airtable's API already emits nicely formatted JSON in `fields` field. 
We only have to name the table columns with correct field names that [jsonjuggler](https://github.com/grandrew/taskjuggler-python/blob/master/taskjuggler_python/jsonjuggler.py) example wrapper expects

```python
from airtable import Airtable
from taskjuggler_python import juggler, jsonjuggler

airtable = Airtable("appA8ZtLosVV7HGXy", "Tasks", api_key="keyAnIuVcuhhkeAkc")

# use DictJuggler example wrapper from jsonjuggler module, directly feed what the API emits in "fields"
JUGGLER = jsonjuggler.DictJuggler([x["fields"] for x in airtable.get_all(view="Work")])

# run taskjuggler and calculate bookings
JUGGLER.run() 

# walk through all tasks objects
for t in JUGGLER.walk(juggler.JugglerTask): 
    airtable.update_by_field("id", t.get_id(), 
        {"booking": t.walk(juggler.JugglerBooking)[0].decode()[0].isoformat()})
# the last line finds first booking in this task, decodes it to datatime list and encodes to isoformat
```

After executing this code you should have time assigned to all of your tasks, none of them overlapping,
respecting dependencies, taking into account default time shifts, appointments and no overwork allowed.

## Writing your own interface

See code for more examples of how to use the interfaces.

# TODO

- **documentation!!**

## TaskJuggler support

- general error reporting support (capture stderr and decode id's)
- emit warnings if e.g. unable to start appointed event due to slipped schedule
- working hours, shifts
- exporting of tjp file; generating reports, gantt charts, etc.
- *deadline (date) - is a check that the task is not scheduled after this date [not in planner - this is a check and can not be enforced]*
- task grouping
- limits dailymax, etc.
- fixed stat time/end time (ALAP/ASAP strats)
    - period for appointments
- non-splittable tasks (`X = effort; limits { maximum Xh }` ??), split punishing
- extensive timezone support
- mark tasks as done / decouple depends

## General enhancements

- Enable pylint with configuration that allows the check to pass (pylint.ini)
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

## Thoughts

- Use logging to predict average performance per day