from ConfigParser import *
import os, re, sys, json, io, atexit
import boto3
import time, datetime, traceback


config = ConfigParser()
config.read('/serverbase.cfg')
# would be nice to to have a common interface whether key:value pairs are environment variables or on a config.ini file
# that way you could run the command from an HTTP request carrying '$SECRET=1234' as a header so that passwords are available for this command and this command only
keys = {}
for section in config.sections():
    sect_dict = dict(config.items(section))
    keys[section.lower()] = sect_dict

class parameters(object):
    def __init__(self, args):
    # if at first you don't succeed,
        try:
            self.args = args
            self.keys = keys
            # input is assumed to be JSON string piped to stdin. If stdin is a terminal, this skips right over, defaulting to an empty JSON object.
            # when called as subprocess in a larger server, isatty will also be false, so it will attempt to read stdin, which will block if there's no end byte available. So pipe a null char for goodness sake.
            self.result = {'stdin': sys.stdin.read() if not sys.stdin.isatty() else "{}" }
            self.input = json.loads(self.result.get('stdin'))
            self.typecast = {
                # type is HTML form input type : followed by python type. file buffers are streams, s3 is an s3Object: .put(Body=STINGIO) to upload
                'number::int':   lambda x: int(x),
                'number::float': lambda x: float(x),

                'date::date':    lambda x: datetime.datetime.strptime(x,'%Y-%m-%d'),                
                
                'text::str':     lambda x: str(x),
                'text::unicode': lambda x: unicode(x),
                'text::tuple':   lambda x: tuple([i.strip() for i in x.split(',')]),
                'text::bool':    lambda x: True if x.lower() == 'true' else False,
                
                'file::buffer':  lambda x: io.open(x, mode='rt'), # named input, assumes file exists, renders as file upload form, open file for reading
                'text::buffer':  lambda x: io.open(x, mode='wb'), # named output, creates a new file (or overwrites existing), renders as text input, open file for writing
                
                'file::s3':      lambda x: boto3.resource('s3', # named input, assumes object exists
                                                aws_access_key_id=self.keys.get('s3').get('aws_access_key_id'), # defaults to None, should look for access key via env or IAM
                                                aws_secret_access_key=self.keys.get('s3').get('aws_secret_access_key')
                                            ).GetObject(x.split('/')[0], x.split('/')[1:]), # should be able to READ this!
                'text::s3':      lambda x: boto3.resource('s3', # named output, creates new object
                                                aws_access_key_id=self.keys.get('s3').get('aws_access_key_id'), # defaults to None, should look for access key via env or IAM
                                                aws_secret_access_key=self.keys.get('s3').get('aws_secret_access_key')
                                            ).Object(self.keys['s3']['bucket'], '%sid/%s/%s' % (self.keys['s3']['prefix'], os.environ.get('USER','undefined'), x))    # you can .put(Body=STRING.IO) to thing!
            
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
                # the key may exist in input, or it may have been defined in the required object
                requiredInput = str(self.input.get(key) or self.args['required'][key]['value'])
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
                    self.stdout("Using '" + requiredInput + "' for " + key + "\n")
                    if('verify' not in self.args['required'][key]):
                        continue
                    checkArgs = re.compile(self.args['required'][key]['verify'])
                    match = checkArgs.findall(requiredInput)
                    if(len(match) == 0):
                        raise SyntaxError(requiredInput + ' did not appear to be ' 
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
                optionalInput = str(self.input.get(key))
                if(optionalInput == None):
                    continue # skip regex check if nothing is there, continue to next key
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
            self.stderr("SYNTAXERROR")
            self.stderr(str(e))
            self.output(self.args)
            traceback.print_exc()
            sys.exit()
        except IndexError as e:
            self.stderr("INDEXERROR")
            self.stderr(str(e))            
            # IndexError means sys.argv didn't hear anything, return argument object
            self.output(self.args)
            traceback.print_exc()
            sys.exit() 
        except KeyError as e:
            self.stderr("KEYERROR")
            self.stderr(str(e))
            self.output(self.args)
            traceback.print_exc()
            sys.exit()
        except ValueError as e:
            self.stderr("VALUEERROR")
            # this means invalid JSON was passed, I think...
            self.stderr(str(e))
            self.output(self.args)
            traceback.print_exc()
            sys.exit()
        except SyntaxWarning as e:
            self.stderr("SYNTAXWARNING")
            
            # print warnings to stderr, they should get displayed but the script will still run
            self.stderr(str(e))
            # Don't exit for SyntaxWarning, just print to stderr

		# even with unbuffered output my JSON was getting concatendated with stdout
        # lineworker.js should be upgraded to handle concatenated JSON
        # but until then, force a gap between retuning error
        # and retuning required/optional parameters

        database = None # database defaults to none if psql or mysql database is not named
        self.database = None
        dbKeys = {}
        # thankfully psycopg2 and pymysql use the same query api
        if self.args.get('psql'):
            import psycopg2 as database
            dbKeys = keys.get(self.args['psql'])
        elif self.args.get('mysql'):
            import pymysql as database
            dbKeys = keys.get(self.args['mysql'])

        # only load connection if database was named. name must correspond with a serverbase.cfg section.
        if database and dbKeys:
            try:
                self.database = database.connect(
                    database=dbKeys['database'],
                    user=dbKeys['user'],
                    host=dbKeys['host'],
                    password=dbKeys['password'],
                    port=int(dbKeys['port'])
                )
                # if I didn't have to coerce port into int I could do database.connect(**dbKeys)
                self.stdout("Connection Established")
            except Exception as e:
                self.stderr("Unable to connect to the database")
                self.stderr(str(e))
                sys.exit()
        # here would be a good place to stop, don't run program if echo param is set
        if self.input.get('echo', None):
            self.output(self.args)
            sys.exit()

    #####  end of constructor ######
    def get(self, key, default):
        return self.__dict__.get(key, default)
    
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

    def outputOnExit(self):
        if self.result:
            print(json.dumps(self.result))
            self.result = None # invalidate object so it only happens once
    
