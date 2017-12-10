#!/bin/bash condavision python=2.7
import pandas,numpy
import pyvalidate

valid = pyvalidate.parameters({
    "required": {
        "rows": {
            "type":"number",
            "default":"10",
            "regex":"^\d+$",
            "desc":"Number of rows"
        },
        "cols": {
            "type":"number",
            "default":"10",
            "regex":"^\d+$",
            "desc":"Number of columns"  
        }
    },
})
locals().update(valid.input)
# Guassian distribution
samples = pandas.DataFrame(numpy.random.rand(rows, cols))
filename = str(rows) + "x" + str(cols) + '.csv'
samples.to_csv(filename)
valid.output("Here's your 3 x 5 random table")
valid.output({ 'src': filename })
