import ConfigParser
import os, re, sys, json, io, atexit
import time, datetime

APPROOT = os.environ.get('APPROOT') or '.' # if APPROOT is not set, 
class parameters(object):
    def __init__(self, args):
        try:        
            self.args = args
            self.result = {}
            self.input = json.loads(sys.argv[1] if len(sys.argv) == 2 else "{}") # incase no object was passed
            self.typecast = {
                # type is HTML form input type : followed by python type. file buffers are streams, s3 is an s3Object: .put(Body=STINGIO) to upload
                'number::int':   lambda x: int(x),
                'number::float': lambda x: float(x),
                
                'text::str':     lambda x: str(x),
                'text::unicode': lambda x: unicode(x),
                'text::tuple':   lambda x: tuple([i.strip() for i in x.split(',')]),
                'text::bool':    lambda x: True if x.lower() == 'true' else False,

                # text input for name of output, file input for file to read from
                'text::buffer':  lambda x: io.open(x, mode='wt'), # if form input was text, open file for writing
                'file::buffer':  lambda x: io.open(x, mode='rt'), # if form input was a file, open file for reading
                # text input for name of s3 output, file s3 for s3 file to read. 
                # 'text:s3':      lambda x: boto3.resource('s3').GetObject(x.split('/')[0], x.split('/')[1:]) # should be able to READ this!
                'file::s3':      lambda x: boto3.resource('s3').Object(x.split('/')[0], x.split('/')[1:]),    # you can .put(Body=STRING.IO) to thing!
            
                'date::date':    lambda x: datetime.datetime.strptime(x,'%Y-%m-%d'),
            }

            for key in self.input:
                # iterate through input object and set value of associated parameter
                # self way when self.args spits the object back, the form will have
                # values set to the input values so you don't have to type them again
                # and its useful as feedback too - what values were used
                # if you sent a key with a typo, you will see its value is undefined
                # defaulting to empty dict so double get doesn't throw error on nonexistant keys
                if(self.args.get('required', {}).get(key) != None):
                    self.args['required'][key]['value'] = self.input[key]
                if(self.args.get('optional',{}).get(key) != None):
                    self.args['optional'][key]['value'] = self.input[key]
            # try to access each required property in the input json
            for key in self.args.get('required', {}):
                requiredInput = self.input.get(key)
                if(requiredInput == None):
                    raise KeyError(key + " is a required parameter.")
                self.output("Using '" + self.input[key] + "' for " + key + "\n")
                checkArgs = re.compile(self.args['required'][key]['verify'])
                match = checkArgs.findall(self.input[key])
                if(len(match) == 0):
                    raise SyntaxError(self.input[key] + ' did not appear to be ' 
                                                        + self.args['required'][key]['desc'] 
                                                        + '\nRegex Failed To Match:\n' 
                                                        + self.args['required'][key]['verify']
                                                        + '\n' + self.args['required'][key].get('help','') + '\n')
                # addtionally, overwrite our input with what the regex extracted
                # so your regex can actually pull out valid matches
                inputType = self.args['required'][key]['type']
                inputValue = match[0]
                self.__dict__[key] = self.typecast[inputType](inputValue)
        
            for key in self.args.get('optional', {}):
                optionalInput = self.input.get(key)
                if(optionalInput == None):
                    continue # skip regex check if nothing is there, continue to next key
                self.output("Using '" + self.input[key] + "' for " + key + "\n")
                checkArgs = re.compile(self.args['optional'][key]['verify'])
                match = checkArgs.findall(self.input[key])
                if(len(match) == 0):
                    raise SyntaxWarning('Optional value ' + self.input[key] 
                                                            + ' will be discarded because it did not match required regex:\n' 
                                                            + self.args['optional'][key]['verify']
                                                            + '\n' + self.args['optional'][key].get('help','') + '\n')

                inputType = self.args['optional'][key]['type']
                inputValue = match[0]
                self.__dict__[key] = self.convert[inputType](inputValue)
        except SyntaxError as e:
            self.error(str(e))
            self.output(self.args)
            sys.exit()
        except IndexError as e:
            # IndexError means sys.argv didn't hear anything, return argument object
            self.output(self.args)
            sys.exit() 
        except KeyError as e:
            self.error(str(e))
            self.output(self.args)
            sys.exit()
        except ValueError as e:
            # this means invalid JSON was passed, I think...
            self.error(str(e))
            self.output(self.args)
            sys.exit()
        except SyntaxWarning as e:
            # print warnings to stderr, they should get displayed but the script will still run
            self.error(str(e))
            # Don't exit for SyntaxWarning, just print to stderr

		# even with unbuffered output my JSON was getting concatendated with stdout
        # lineworker.js should be upgraded to handle concatenated JSON
        # but until then, force a gap between retuning error
        # and retuning required/optional parameters

        database = None # database defaults to none if psql or mysql database is not named
        # thankfully psycopg2 and pymysql use the same query api
        if self.args.get('psql') != None:
            import psycopg2 as database
        elif self.args.get('mysql') != None:
            import pymysql as database

        if(database): # only load connection if database was named. name must correspond with a credentials.ini section.
            dbKeys = ConfigParser.ConfigParser()
            dbKeys.read('credentials.ini') # assumed that working directory is location of spider is location of credentials...
            try:
                self.conn = psycopg2.connect("dbname='%(database)s' port='%(port)s' user='%(user)s' \
                    host='%(host)s' password='%(password)s'" % dict(dbKeys.items(database)))
                self.output("Connection Established")
            except:
                self.output({"stderr":"Unable to connect to the database"})
                sys.exit()


    def cursor(self): # a getter method to return a database cursor
        if(self.args.get('database')):        
            return self.conn.cursor()
        else: 
            raise Exception("database parameter was not defined, so there is no connection.")

    def error(self, string):
        self.output({"stderr": string})
    
    def output(self, stringOrDict):
        # strings passed to output will be wrapped in an object with key 'stdout'
        newData = stringOrDict if type(stringOrDict) == dict else {"stdout": stringOrDict + '\n'}
        for key in newData:
            if self.result.get(key) == None:
                # create key if it doesn't exist
                self.result[key] = newData[key]
            else:
                # append new data to existing key
                self.result[key] += newData[key]
        # output is buffered by default,
        # if that's the case, wait til program exit to print one single object
        # but if PYTHONUNBUFFERED is specified, print out each piece of data as it comes as separate JSON object
        # useful for streaming API
        if os.environ.get('PYTHONUNBUFFERED'):
            print(json.dumps(newData))
        elif len(atexit._exithandlers) == 0:
            atexit.register(self.outputOnExit)

    def get(self, key, default):
        return self.__dict__.get(key, default)
    
    def outputOnExit(self):
        print(json.dumps(self.result))
# it'd be pretty cool if self checked the PYTHONUNBUFFERED variable, 
# and its assumed that pyvalidate is running inside an event based API if output is unbuffed
# and prints every time output is called, 
# but if PYTHONUNBUFFERED was unset, then assume that self is a post request that needs to be answered 
# with a single JSON object, so, accumulate messages to stdout, print it all on exit
# atexit.register(outputAll), something like that