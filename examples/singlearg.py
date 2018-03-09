#!/usr/bin/env python
#!/usr/bin/sudo condavision
# must be run with pyvalidate in PYTHONPATH
# condavision uses PYTHONPATH to check dependencies
import pandas,numpy
import StringIO, time, os
import pyvalidate

valid = pyvalidate.parameters({
    "database": {
        "mysql": "labsdb",
    },
    "arg": {
        "type":"number::int",
        "info":"number of rows and columns",
        "placeholder":"for example: 3",
        "verify":"^\d+$"
    },
    "s3upload": {
        "info": "Where should the result be saved?",
        "type": "text::s3",
        "value": 'example' + str(int(time.time())) + '.csv',
        "verify": "^[A-Za-z0-9._]+$" # restrict filename if you want
    }
    "labels": {
        "type":"text::bool",
        "info":"Whether to print row and column labels",
        "verify":"(?i)^(true|false)$",
        "placeholder": "True or False"
    }
})
# Guassian distribution
samples = pandas.DataFrame(numpy.random.rand(valid.arg, valid.arg))
valid.s3upload.put(Body=samples.to_csv())
valid.output({'downloads3': valid.s3upload.pathname})