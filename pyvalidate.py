import ConfigParser
import psycopg2
import os, re, sys, json, io
import time, datetime
import atexit

class parameters(object):
    def __init__(this, args):
        # try:        
        this.args = args
        this.input = json.loads(sys.argv[1])
        # I wanted a switch statement to convert each parameters based on the type, don't have a plan on using floats as input yet... will have to think about unicode
        this.typecast = {
            # type is HTML form input type : followed by python type
            'number:int': lambda v: int(v),
            'number:float': lambda v: float(v),
            
            'text:str': lambda v: str(v),
            'text:unicode': lambda v: unicode(v),
            'text:tuple': lambda v: tuple([x.strip() for x in v.split(',')]),
            'text:bool': lambda v: True if v.lower() == 'true' else False,

            'text:buffer': lambda v: io.open(v, mode='wt') # if form input was text, open file for writing
            'file:buffer': lambda v: io.open(v, mode='rt') # if form input was a file, open file for reading
            
            'date:date': lambda v: datetime.datetime.strptime(v,'%Y-%m-%d'),
        }
        
        for key in this.input:
            # iterate through input object and set value of associated parameter
            # this way when this.args spits the object back, the form will have
            # values set to the input values so you don't have to type them again
            # and its useful as feedback too - what values were used
            # if you sent a key with a typo, you will see its value is undefined
            # defaulting to empty dict so double get doesn't throw error on nonexistant keys
            if(this.args.get('required', {}).get(key) != None):
                this.args['required'][key]['value'] = this.input[key]
            if(this.args.get('optional',{}).get(key) != None):
                this.args['optional'][key]['value'] = this.input[key]
        # try to access each required property in the input json
        for key in this.args.get('required', {}):
            requiredInput = this.input.get(key)
            if(requiredInput == None):
                raise KeyError(key + " is a required parameter.")
            this.output("Using '" + this.input[key] + "' for " + key + "\n")
            checkArgs = re.compile(this.args['required'][key]['regex'])
            match = checkArgs.findall(this.input[key])
            if(len(match) == 0):
                raise SyntaxError(this.input[key] + ' did not appear to be ' 
                                                    + this.args['required'][key]['desc'] 
                                                    + '\nRegex Failed To Match:\n' 
                                                    + this.args['required'][key]['regex']
                                                    + '\n' + this.args['required'][key].get('help','') + '\n')
            # addtionally, overwrite our input with what the regex extracted
            # so your regex can actually pull out valid matches
            inputType = this.args['required'][key]['type']
            inputValue = match[0]
            this.__dict__[key] = this.typecast[inputType](inputValue)
    
        for key in this.args.get('optional', {}):
            optionalInput = this.input.get(key)
            if(optionalInput == None):
                continue # skip regex check if nothing is there, continue to next key
            this.output("Using '" + this.input[key] + "' for " + key + "\n")
            checkArgs = re.compile(this.args['optional'][key]['regex'])
            match = checkArgs.findall(this.input[key])
            if(len(match) == 0):
                raise SyntaxWarning('Optional value ' + this.input[key] 
                                                        + ' will be discarded because it did not match required regex:\n' 
                                                        + this.args['optional'][key]['regex']
                                                        + '\n' + this.args['optional'][key].get('help','') + '\n')

            inputType = this.args['optional'][key]['type']
            inputValue = match[0]
            this.__dict__[key] = this.convert[inputType](inputValue)
        # except SyntaxError as e:
        #     this.args["stderr"] = str(e)
        #     this.output(this.args)
        #     sys.exit()
        # except IndexError as e:
        #     # IndexError means sys.argv didn't hear anything, return argument object
        #     this.output(this.args)
        #     sys.exit() 
        # except KeyError as e:
        #     # This means keys weren't provided, echo the arg objet
        #     this.args["stderr"] = str(e)
        #     this.output(this.args)            
        #     sys.exit()
        # except SyntaxWarning as e:
        #     # print warnings to stderr, they should get displayed but the script will still run
        #     this.args["stderr"] = str(e)
        #     # Don't exit for SyntaxWarning, just print to stderr

		# even with unbuffered output my JSON was getting concatendated with stdout
        # Offspring.js should be upgraded to handled this
        # but until then, force a gap between retuning error
        # and retuning required/optional parameters


        if(this.args.get('mysql') != None):
            credentialpath = os.environ['SPIDERROOT'] + '/' + this.args['database'] + '/credentials.ini'
            dbKeys = ConfigParser.ConfigParser()
            dbKeys.read(credentialpath)
            try:
                this.conn = psycopg2.connect("dbname='%(database)s' port='%(port)s' user='%(user)s' \
                    host='%(host)s' password='%(password)s'" % dict(dbKeys.items('comscore')))
                this.output("Connection Established")
            except:
                this.output({"stderr":"Unable to connect to the database"})
                sys.exit()

    def cursor(this):
        if(this.args['database'] != None):        
            return this.conn.cursor()
        else: 
            raise Exception("database parameter was not defined, so there is no connection.")

    def output(this, stringOrDict):
        # print stdout object if passed a string, else jsonify the dictionary passed to output
        print(json.dumps({"stdout": stringOrDict + '\n'} if type(stringOrDict) == str else stringOrDict))
        
        # if os.environ['PYTHONUNBUFFERED']:
        #     print(json.dumps({"stdout": stringOrDict + '\n'} if type(stringOrDict) == str else stringOrDict))
        # else:
            # this.whole 
            # merge object to return 
    def get(this, key, default):
        return this.__dict__.get(key, default)
    
    # def outputOnExit(this):
    #     # print(json.dumps(this.__dict__.))
    #     print(this.__dict__)
# it'd be pretty cool if this checked the PYTHONUNBUFFERED variable, 
# and its assumed that pyvalidate is running inside an event based API if output is unbuffed
# and prints every time output is called, 
# but if PYTHONUNBUFFERED was unset, then assume that this is a post request that needs to be answered 
# with a single JSON object, so, accumulate messages to stdout, print it all on exit
# atexit.register(outputAll), something like that