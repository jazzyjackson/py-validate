#!/bin/bash condavision
# must be run with pyvalidate in PYTHONPATH
# condavision uses PYTHONPATH to check dependencies
import pandas,numpy
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
filename = str(valid.rows) + "x" + str(valid.cols) + '.csv'
samples.to_csv(
    filename, 
    index=valid.get('labels',False),  # print row labels
    header=valid.get('labels',False)) # print column labels
valid.output("Here's your " + str(valid.rows) + " x " + str(valid.cols) + " random table")
valid.output({'download': filename })