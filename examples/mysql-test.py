#!/usr/bin/python
import pymysql, pandas, os
import pyvalidate

valid = pyvalidate.parameters({
    "database":{
        "mysql": "labsdb"
    },
    "s3upload": {
        "type": "text::s3",
        "info": "Where should the result be saved?",
        "value": 'aubi_utilties.csv',
        "verify": "^[A-Za-z0-9._]+$" # restrict filename if you want
    }
})

mysql = valid.database.cursor()

mysql.execute("SELECT * FROM aubi_utilities")
df = pandas.DataFrame(list(mysql.fetchall()))
valid.s3upload.put(Body=df.to_csv())

fulls3path = '/id/%s/%s' % (os.environ.get('USER', 'undefined'), valid.args['required']['s3upload']['value'])
valid.output({'downloads3': fulls3path})