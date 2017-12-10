#!/bin/bash condavision python=2.7
import pandas,numpy
import pyvalidate

valid = pyvalidate.parameters({
    "required": {
        "rows": {
            "input":"number",
            "type":"int",
            "example":"10",
            "regex":"^\d+$",
            "info":"Number of rows"
        },
        "cols": {
            "input":"number",
            "type":"int",        
            "example":"10",
            "regex":"^\d+$",
            "info":"Number of columns"  
        },
    },
    "optional": {
        "labels": {
            "input":"text",
            "type":"bool",
            "example":"true or false",
            "regex":"(?i)^(true|false)$",
            "info":"Whether to print row and column labels"  
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