#!/usr/bin/env python
#!/usr/bin/sudo condavision
# must be run with pyvalidate in PYTHONPATH
# condavision uses PYTHONPATH to check dependencies
import pandas,numpy
import StringIO, time, os
import pyvalidate

valid = pyvalidate.parameters({
    "mysql": "labsdb",
    "required": {
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
        "s3upload": {
            "info": "Where should the result be saved?",
            "type": "text::s3",
            "value": 'example' + str(int(time.time())) + '.csv',
            "verify": "^[A-Za-z0-9._]+$" # restrict filename if you want
        }
    },
    "optional": {
        "labels": {
            "type":"text::bool",
            "info":"Whether to print row and column labels",
            "verify":"(?i)^(true|false)$",
            "placeholder": "True or False"
        }
    }
})
# Guassian distribution
samples = pandas.DataFrame(numpy.random.rand(valid.rows, valid.cols))
valid.s3upload.put(Body=samples.to_csv())

fulls3path = '/id/%s/%s' % (os.environ.get('USER', 'undefined'), valid.args['required']['s3Object']['value'])
valid.output({'downloads3': fulls3path})
