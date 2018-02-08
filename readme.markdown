# PyValidate
### Turn your python code into a web API that talks JSON

PyValidate allows you to write an informative object that ensures arguments look the way the script expects them to look before attempting to run the program. It is written to solve the problem of complex data science queries failing half way through a job because a string contained a character it wasn't supposed to. Much better if things fail right away, especially if you get a message explaining what was expected of you.

Paired with Poly-Int, you can generate a web interface with proper form necessary (including date, number, and text inputs depending on your specified type) and customize how the results are displayed.

Paired with ChatScript, your chatbot personality can ping a python script to find out what it needs, collect the necessary variables through conversation, and execute the script once it has the required parameters.

Paired with condavision, you can create new scripts that will run on the server without having to think about system configuration and dependencies.

## Usage
Make sure pyvalidate.py is sitting in a folder on your PYTHONPATH and import it to any python script. The class contructor is named "parameters" so my suggested pattern is to initialize it as follows, so you end up with a 'valid' instance to interact with.

### Initialize
```py
import pyvalidate
valid = pyvalidate.parameters({
    "required": {
        "rows": {
            "info":"Number of rows"
            "type":"number:int",
            "valid":"^\d+$",
            "placeholder":"10",
        },
        "cols": {
            "info":"Number of columns"  
            "type":"numbe:intr",
            "valid":"^\d+$",
            "placeholder":"5",
        }
    },
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
    "required": {
        "rows":{},
        "cols":{},
        "file": {
            "info": "Where should the result be saved?"
            "type": "text:buffer",
            "value": 'example' + str(int(time.time())) + '.csv',
            "verify": "^[A-Za-z0-9]+$" # restrict filename if you want
            }
        }
    },
})
```


## Interaction as an API

If the program is called with no input, the entire object is returned and the sender of an empty request will be able to see what's required of them.

In order to call the program with the named parameters, a JSON string may be piped to stdin, or passed as the first argument. Either way, py-validate goes through the keys of that object to see if it has a 'required' key, and then inspects each parameter therein, testing the value with the 'verify' regex, exiting if there's no match. 

The JSON input, at the top level, must have a 'required' object, and may also have an 'optional' object. It can also contain an 'echo' parameter. If 'echo' contains a value that Python's Boolean constructor coerces to 'true', then all the parameters are verified, and a filled out object is echo'd back, and the program exits without running. You might call it a 'dry-run'. So if you provided all the required parameters, your object will be echoed back and contain 'value' keys and you'll know that you're ready to go.

In the rest of the program, you can refer to the parameters like :

Messages can be passed back as JSON using `valid.stdout()` and `valid.stderr()`. If the program is being run as a streaming API, an environment variable should be set on PYTHONUNBUFFERED so results are printed right away. Otherwise, all the messages are collected into a single output object that is printed on program exit.

