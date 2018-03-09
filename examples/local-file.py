#!/usr/bin/env python
# must be run with pyvalidate in PYTHONPATH
# condavision uses PYTHONPATH to check dependencies
import pandas,numpy
import StringIO, time
import pyvalidate

valid = pyvalidate.parameters({
    "rows": {
        "type":"number::int",
        "info":"number of rows",
        "placeholder":"for example: 3",
        "verify":"^\d+$"
    },
    "cols": {
        "type":"number::int",
        "info":"number of columns",
        "placeholder":"for example: 5",
        "verify":"^\d+$"
    },
    "file": {
        "info": "Where should the result be saved?",
        "type": "text::buffer",
        "value": 'example' + str(int(time.time())) + '.csv',
        "verify": "^[A-Za-z0-9.-]+$" # restrict filename if you want
    },
    "labels": {
        "type":"text::bool",
        "info":"Whether to print row and column labels",
        "verify":"(?i)^(true|false)$",
        "placeholder": "True or False"
    }
})
# Guassian distribution
samples = pandas.DataFrame(numpy.random.rand(valid.rows, valid.cols))
valid.file.write(samples.to_csv(
    index=valid.get('labels', False),
    header=valid.get('labels', False),
))

valid.output({'download': valid.file.name })