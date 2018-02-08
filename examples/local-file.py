#!/usr/bin/sudo condavision
# must be run with pyvalidate in PYTHONPATH
# condavision uses PYTHONPATH to check dependencies
import pandas,numpy
import StringIO, time
import pyvalidate

valid = pyvalidate.parameters({
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
        "file": {
            "info": "Where should the result be saved?",
            "type": "text::buffer",
            "value": 'example' + str(int(time.time())) + '.csv',
            "verify": "^[A-Za-z0-9]+$" # restrict filename if you want
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
# print(valid.file)
print(valid.args['required']['file']['value'])
# samples = pandas.DataFrame(numpy.random.rand(valid.rows, valid.cols))
# samples.to_csv(
#     valid.file,
#     index=valid.get('labels', False),
#     header=valid.get('labels', False)
# )

# valid.file refers to the result of io open
# valid.args.file.value refers to the value of the arguments object, the filename

# valid.output("Here's your " + str(valid.rows) + " x " + str(valid.cols) + " random table")
# valid.output({'download': filename })