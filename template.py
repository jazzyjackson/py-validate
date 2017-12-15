#!/bin/bash condavision python=2.7
import pandas,numpy
import pyvalidate

valid = pyvalidate.parameters({
    "required": {
        "rows": {
            "info":"Number of rows"
            "type":"number:int",
            "verify":"^\d+$",
            "placeholder":"3"
        },
        "cols": {
            "info":"Number of columns"  
            "type":"number:int",
            "verify":"^\d+$",
            "placeholder":"5"
        },
    },
    "optional": {
        "labels": {
            "info":"Whether to print row and column labels"  
            "type":"text:bool",
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
valid.output("Here's your " + str(valid.rows) + " x " + str(valid.cols) +" random table")
valid.output({ 'src': filename })