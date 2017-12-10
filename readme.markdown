# PyValidate
### Turn your python code into a web API that talks JSON

PyValidate allows you to write an informative object that checks that arguments look the way the script expects them to look before attempting to run the rest of the program. It is written to solve the problem of complex data science queries failing half way through a job because a string contained a character it wasn't supposed to. Much better if things fail right away, especially if you get a message explaining what was expected of you.

It works like this: you import the module and initialize it by 
```py
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

```
If the program is called with no input, the entire object is returned.
If the program is called with a JSON object, it goes through the keys of that object to see if it has required parameters, and then inspects each parameter to make sure the regex matches. If any of this fails, the program exits and you're returned JSON which also includes an added 'input' key for each parameter representing the input it tried to use.

TODO: If your regex includes matching groups, the input is replaced with the match allowing for simple input cleansing and prepartion. 

In the rest of the program, you can refer to the parameters like :
```py
samples = pandas.DataFrame(numpy.random.rand(valid.rows, valid.cols))
```
Messages can be passed back as JSON using `valid.output()` and `valid.error`. If the program is being run as a streaming API, an environment variable should be set on PYTHONUNBUFFERED so results are printed right away. Otherwise, all the messages are collected into a single output object that is printed on program exit.

Paired with Poly-Int Polymorphic Interface, you can have a web interface that generates the proper form necessary (including date, number, and text inputs depending on your specified type) and allows you to customize the presentation of the result.

Paired with ChatScript, you can ping a python script to find out what it needs, collect the necessary variables through conversation, and execute the script passing in required and optional variables.