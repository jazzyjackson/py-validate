from ConfigParser import *
import os, re, sys, json, io, atexit, boto3
import time, datetime

config = ConfigParser()
config.read('/credentials.ini')

keys = {}
for section in config.sections():
    sect_dict = dict(config.items(section))
    keys[section.lower()] = sect_dict

class parameters(object):
    def __init__(self, args):
        try:
            # would be nice that if json.loads fails, just set that value as 'input.stdin' - if that matches your required object your fine for one parameters. just make sure its passed as one parameter.
            # should also read stdin, allowing the JSON to be posted as the body of an HTTP request.
            # stdin = readline
            self.args = args
            self.result = {'stdin': sys.argv[1] if len(sys.argv) == 2 else "{}"} # incase no object was passed
            self.input = json.loads(self.result['stdin']) 
            self.typecast = {
                # type is HTML form input type : followed by python type. file buffers are streams, s3 is an s3Object: .put(Body=STINGIO) to upload
                'number::int':   lambda x: int(x),
                'number::float': lambda x: float(x),
                
                'text::str':     lambda x: str(x),
                'text::unicode': lambda x: unicode(x),
                'text::tuple':   lambda x: tuple([i.strip() for i in x.split(',')]),
                'text::bool':    lambda x: True if x.lower() == 'true' else False,

                # text input for name of output, file input for file to read from
                'text::buffer':  lambda x: io.open(x, mode='wb'), # if form input was text, open file for writing
                'file::buffer':  lambda x: io.open(x, mode='rt'), # if form input was a file, open file for reading
                # text input for name of s3 output, file s3 for s3 file to read. 
                # 'text:s3':      lambda x: boto3.resource('s3').GetObject(x.split('/')[0], x.split('/')[1:]) # should be able to READ this!
                'text::s3':      lambda x: boto3.resource('s3', 
                                                aws_access_key_id=keys['s3']['aws_access_key_id'], 
                                                aws_secret_access_key=keys['s3']['aws_secret_access_key']
                                            ).Object(keys['s3']['bucket'], '%sid/%s/%s' % (keys['s3']['prefix'], os.environ.get('USER','undefined'), x)),    # you can .put(Body=STRING.IO) to thing!
            
                'date::date':    lambda x: datetime.datetime.strptime(x,'%Y-%m-%d'),
            }

            for key in self.input:
                # iterate through input object and set value of associated parameter
                # self way when self.args spits the object back, the form will have
                # values set to the input values so you don't have to type them again
                # and its useful as feedback too - what values were used
                # if you sent a key with a typo, you will see its value is undefined
                # defaulting to empty dict so double get doesn't throw error on nonexistant keys
                if self.args.get('required', {}).get(key):
                    self.args['required'][key]['value'] = self.input[key]
                if self.args.get('optional', {}).get(key):
                    self.args['optional'][key]['value'] = self.input[key]
            # try to access each required property in the input json
            for key in self.args.get('required', {}):
                requiredInput = self.input.get(key)
                inputValue = None
                inputType = self.args['required'][key]['type'] # if there's no type, should throw error, malformed input
                # this if not/if/else/else/if/else either sets input value or throws an error. godspeed.
                if not requiredInput:
                    if self.args.get('required',{}).get(key, {}).get('value', None):
                        inputValue = self.args['required'][key]['value']
                        self.stdout("Using '" + inputValue + "' for " + key + "\n")
                    else:
                        raise KeyError(key + " is a required parameter.")
                else:
                    self.stdout("Using '" + self.input[key] + "' for " + key + "\n")
                    checkArgs = re.compile(self.args['required'][key]['verify'])
                    match = checkArgs.findall(self.input[key])
                    if(len(match) == 0):
                        raise SyntaxError(self.input[key] + ' did not appear to be ' 
                                                            + self.args['required'][key]['info'] 
                                                            + '\nRegex Failed To Match:\n' 
                                                            + self.args['required'][key]['verify']
                                                            + '\n' + self.args['required'][key].get('help','') + '\n')
                    else:
                        inputValue = match[0]
                    
                # only invoke the functions if we're not echoing
                # otherwise if we're dealing in s3 it's gonna open connections
                if not self.input.get('echo'):
                    self.__dict__[key] = self.typecast[inputType](inputValue)
        
            for key in self.args.get('optional', {}):
                optionalInput = self.input.get(key)
                if(optionalInput == None):
                    continue # skip regex check if nothing is there, continue to next key
                self.stdout("Using '" + self.input[key] + "' for " + key + "\n")
                checkArgs = re.compile(self.args['optional'][key]['verify'])
                match = checkArgs.findall(self.input[key])
                if(len(match) == 0):
                    raise SyntaxWarning('Optional value ' + self.input[key] 
                                                            + ' will be discarded because it did not match required regex:\n' 
                                                            + self.args['optional'][key]['verify']
                                                            + '\n' + self.args['optional'][key].get('help','') + '\n')

                inputType = self.args['optional'][key]['type']
                inputValue = match[0]
                if not self.input.get('echo'):
                    self.__dict__[key] = self.typecast[inputType](inputValue)

        except SyntaxError as e:
            self.stderr(str(e))
            self.output(self.args)
            sys.exit()
        except IndexError as e:
            # IndexError means sys.argv didn't hear anything, return argument object
            self.output(self.args)
            sys.exit() 
        except KeyError as e:
            self.stderr(str(e))
            self.output(self.args)
            sys.exit()
        except ValueError as e:
            # this means invalid JSON was passed, I think...
            self.stderr(str(e))
            self.output(self.args)
            sys.exit()
        except SyntaxWarning as e:
            # print warnings to stderr, they should get displayed but the script will still run
            self.stderr(str(e))
            # Don't exit for SyntaxWarning, just print to stderr

		# even with unbuffered output my JSON was getting concatendated with stdout
        # lineworker.js should be upgraded to handle concatenated JSON
        # but until then, force a gap between retuning error
        # and retuning required/optional parameters

        database = None # database defaults to none if psql or mysql database is not named
        dbKeys = {}
        # thankfully psycopg2 and pymysql use the same query api
        if self.args.get('psql'):
            import psycopg2 as database
            dbKeys = keys.get(self.args['psql'])
        elif self.args.get('mysql'):
            import pymysql as database
            dbKeys = keys.get(self.args['mysql'])

        # only load connection if database was named. name must correspond with a credentials.ini section.
        if database and dbKeys:
            try:
                self.database = database # expose database for pdsql_readquery
                self.conn = database.connect(
                    database=dbKeys['database'],
                    user=dbKeys['user'],
                    host=dbKeys['host'],
                    password=dbKeys['password']
                )
                self.stdout("Connection Established")
            except:
                self.stderr("Unable to connect to the database")
                sys.exit()
        # here would be a good place to stop 
        if self.input.get('echo', None):
            self.output(self.args)
            sys.exit()


    def cursor(self): # a getter method to return a database cursor
        if self.args.get('mysql') or self.args.get('psql'):        
            return self.conn.cursor() # or maybe I should just 'try'
        else: 
            raise Exception("database parameter was not defined, so there is no connection.")

    def stderr(self, string):
        self.output({"stderr": string})

    def stdout(self, string):
        self.output({"stdout" :string})

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
        else:
            atexit.register(self.outputOnExit)

    def get(self, key, default):
        return self.__dict__.get(key, default)
    
    def outputOnExit(self):
        if self.result:
            print(json.dumps(self.result))
            self.result = None # invalidate object so it only happens once
    
