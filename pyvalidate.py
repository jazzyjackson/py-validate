import sys
import ConfigParser
import psycopg2
import os
import re
import sys
import json
import time

class parameters:
    def __init__(self, args):
        try:
            self.args = args
            self.input = json.loads(sys.argv[1])
            for key in self.input:
                # iterate through input object and set value of associated parameter
                # this way when self.args spits the object back, the form will have
                # values set to the input values so you don't have to type them again
                # and its useful as feedback too - what values were used
                # if you sent a key with a typo, you will see its value is undefined
                if(self.args['required'].get(key) != None):
                    self.args['required'][key]['value'] = self.input[key]
                if(self.args['optional'].get(key) != None):
                    self.args['optional'][key]['value'] = self.input[key]
            # try to access each required property in the input json
            for key in self.args['required']:
                requiredInput = self.input.get(key)
                if(requiredInput == None):
                    raise KeyError(key + " is a required parameter.")
                self.output("Using '" + self.input[key] + "' for " + key + "\n")
                checkArgs = re.compile(self.args['required'][key]['regex'])
                match = checkArgs.findall(self.input[key])
                if(len(match) == 0):
                    raise SyntaxError(self.input[key] + ' did not appear to be ' 
                                                      + self.args['required'][key]['desc'] 
                                                      + '\nRegex Failed To Match:\n' 
                                                      + self.args['required'][key]['regex']
                                                      + '\n' + self.args['required'][key]['help'] + '\n')
                # addtionally, overwrite our input with what the regex extracted
                # so your regex can actually pull out valid matches
                self.input[key] = match[0]
            for key in self.args['optional']:
                optionalInput = self.input.get(key)
                if(optionalInput == None):
                    continue # skip regex check if nothing is there, continue to next key
                self.output("Using '" + self.input[key] + "' for " + key + "\n")
                checkArgs = re.compile(self.args['optional'][key]['regex'])
                match = checkArgs.findall(self.input[key])
                if(len(match) == 0):
                    raise SyntaxWarning('Optional value ' + self.input[key] 
                                                          + 'will be discarded because it did not match required regex:\n' 
                                                          + self.args['optional'][key]['regex']
                                                          + '\n' + self.args['optional'][key]['help'] + '\n')
                self.input[key] = match[0]                
        except SyntaxError as e:
            self.args["stderr"] = str(e)
            self.output(self.args)
            sys.exit()
        except IndexError as e:
            # IndexError means sys.argv didn't hear anything, return argument object
            self.output(self.args)
            sys.exit() 
        except KeyError as e:
            # This means keys weren't provided, echo the arg objet
            self.args["stderr"] = str(e)
            self.output(self.args)            
            sys.exit()
        except SyntaxWarning as e:
            # print warnings to stderr, they should get displayed but the script will still run
            self.args["stderr"] = str(e)
            # Don't exit for SyntaxWarning, just print to stderr

		# even with unbuffered output my JSON was getting concatendated with stdout
        # Offspring.js should be upgraded to handled this
        # but until then, force a gap between retuning error
        # and retuning required/optional parameters
        time.sleep(0.25)
        self.output(self.args)
        time.sleep(0.25)

        if(self.args.get('mysql') != None):
            credentialpath = os.environ['SPIDERROOT'] + '/' + self.args['database'] + '/credentials.ini'
            dbKeys = ConfigParser.ConfigParser()
            dbKeys.read(credentialpath)
            try:
                self.conn = psycopg2.connect("dbname='%(database)s' port='%(port)s' user='%(user)s' \
                    host='%(host)s' password='%(password)s'" % dict(dbKeys.items('comscore')))
                self.output("Connection Established")
            except:
                self.output({"stderr":"Unable to connect to the database"})
                sys.exit()

    def cursor(self):
        if(self.args['database'] != None):        
            return self.conn.cursor()
        else: 
            raise Exception("database parameter was not defined, so there is no connection.")

    def output(self, stringOrDict):
        # print stdout object if passed a string, else jsonify the dictionary passed to output
        if os.environ['PYTHONUNBUFFERED']:
            print(json.dumps({"stdout": stringOrDict + '\n'} if type(stringOrDict) == str else stringOrDict))
        else:
            # self.whole 
            # merge object to return 
            # atexit.register(self.outputOnExit)
    
    def outputOnExit(self):
        print(json.dumps(self.whole))
# it'd be pretty cool if this checked the PYTHONUNBUFFERED variable, 
# and its assumed that pyvalidate is running inside an event based API if output is unbuffed
# and prints every time output is called, 
# but if PYTHONUNBUFFERED was unset, then assume that this is a post request that needs to be answered 
# with a single JSON object, so, accumulate messages to stdout, print it all on exit
# atexit.register(outputAll), something like that