import pymysql, pandas

valid = pyvalidate.parameters({
    "database": "labsdb"    
    "required": {
        "day": {
            "type":"date::date",
            "info":"what date should I query the logs",
            "placeholder":"for example: 3",
            "verify":"^\d+$"
        },
    }
})

mysql = valid.cursor()
mysql.execute("SELECT * FROM aubi_logs WHERE timestamp > %s", (valid.day,))
for row in mysql.fetchall():
    valid.stdout(row)