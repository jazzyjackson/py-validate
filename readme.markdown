# PyValidate
### bad input fails fast: regex validation + type coercion

PyValidate allows you to write an informative object that ensures arguments look the way the script expects them to look before attempting to run the program. You specify what python type you need input to be coerced to, and you can optionally specifiy regex to throw an error if input doesn't match.

It is written to solve the problem of complex data science queries failing half way through a job because a string contained a character it wasn't supposed to. Much better if things fail right away, especially if you get a message explaining what was expected of you.

Paired with [ChatScript](https://github.com/bwilcox-1234/ChatScript), your chatbot personality can communicate via JSON with a python script to find out what it needs, collect the necessary variables through conversation, and execute the script once it has the required parameters.

Paired with [condavision](https://github.com/jazzyjackson/condavision), you can create new scripts without having to keep tabs on what python dependencies / version your server is running.

(TODO:) Paired with [mixininterface](https://github.com/jazzyjackson/mixininterface), you can auto-generate a web form including date, number, and text inputs depending on your specified type and customize how the results are displayed.

## Usage
Make sure pyvalidate.py is sitting in a folder on your PYTHONPATH and import it to any python script. The class contructor is named "parameters" so my suggested pattern is to initialize it as follows, so you end up with a 'valid' instance to interact with.

### Initialize
First step is to create an object that will act as a dictionary of variables you'll use in the rest of the program. Top level keys are your own names -- but `database` is a keyword with special treatment (see Databases below).

The properties of each object must include 'type' in the form 'HTML-form-type :: python type', check out the typecast functions in pyvalidate.py for the full list of combinations.

```py
import pyvalidate
valid = pyvalidate.parameters({
    "rows": {
        "info":"Number of rows"
        "type":"number::int",
        "verify":"^\d+$",
        "placeholder":"10",
    },
    "cols": {
        "info":"Number of columns"  
        "type":"numbe::int",
        "verify":"^\d+$",
        "placeholder":"5",
    }
})

```
### Get Parameters
Now in the rest of your program, you can refer to the validated parameters like so: 

```py
samples = pandas.DataFrame(numpy.random.rand(valid.rows, valid.cols))
```

### Write local files
_Full example in examples/localfile.py_
```py
import pyvalidate
valid = pyvalidate.parameters({
    # file_out is not a keyword, this is called whatever you want
    "file_out": { 
        "info": "Where should the result be saved?"
        # text::buffer is the part that tells pyvalidate to return a file buffer
        "type": "text::buffer", 
        # provide a default value
        "value": 'example' + str(int(time.time())) + '.csv', 
         # restrict filename if you want
        "verify": "^[A-Za-z0-9]+$"
    }
})

valid.file_out.write("Hello I will become one with the disk")
```

### Connecto mysql or psql databases
If one of your top level keys is called 'database', py-validate creates a database connection. Declare your database like so:
```py
import pyvalidate
valid = pyvalidate.parameters({
    "database": { 
        "psql": "yournamehere"
    },
    "search-term": {
        "type": "text::str"
    }
})
```
When py-validate encounters the database key, it checks whether a psql key exists and imports psycopg2, or if a mysql key exists and imports pymysql. Then, it uses the value of that key as the name of a section of a local configuration file in ini format. By default py-validate loads serverbase.cfg from the root of the computer, but you can edit this to point where you want. (TODO:)It would be better if this checked environment variables for location of this file, or iteratively look for a config.ini up the folder heirarchy.

The config file should include all keys needed to open a connection: host, port, user, database, password. 

Once that succeeds, in the rest of of your program you can interact with database just like the rest of the valid keys:
```py
with valid.database.cursor() as conn:
    conn.execute("SELECT * FROM table WHERE something == %(search-term)s", valid)
```

Note you can pass the valid object to execute in order to interpolate values you declared on initialization.

## Interaction as an API

If the program is called with no input, the entire object is returned and the sender of an empty request will be able to see what's required of them.

In order to call the program with the named parameters, a JSON string may be piped to stdin, or passed as the first argument. Either way, py-validate goes through the keys of that object to see if it has a 'required' key, and then inspects each parameter therein, testing the value with the 'verify' regex, exiting if there's no match. 

The JSON input, at the top level, must have a 'required' object, and may also have an 'optional' object. It can also contain an 'echo' parameter. If 'echo' contains a value that Python's Boolean constructor coerces to 'true', then all the parameters are verified, and a filled out object is echo'd back, and the program exits without running. You might call it a 'dry-run'. So if you provided all the required parameters, your object will be echoed back and contain 'value' keys and you'll know that you're ready to go.

In the rest of the program, you can refer to the parameters like :

Messages can be passed back as JSON using `valid.stdout()` and `valid.stderr()`. If the program is being run as a streaming API, an environment variable should be set on PYTHONUNBUFFERED so results are printed right away. Otherwise, all the messages are collected into a single output object that is printed on program exit.

