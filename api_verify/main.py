'''SMART API Verifier main controller'''
# Developed by: Nikolai Schwertner
#
# Revision history:
#     2012-02-24 Initial release

# Import some general modules
import json
import urllib
import web
import os
import sys

# Add the current directory to the system path so that mod_py could
# load the local modules
abspath = os.path.dirname(__file__)
sys.path.append(abspath)

# Import the local smart client modules and components
from smart_client import oauth
from smart_client.smart import SmartClient
from smart_client.common import rdf_ontology
from smart_client.generate_api import call_name

# Import the application settings
from settings import APP_PATH

# Import the testing framework utilities
from tests import runTest, getMessages

# Default configuration settings for the SMART client
SMART_SERVER_OAUTH = {
#    'consumer_key': 
    'consumer_secret': 'smartapp-secret'
}

SMART_SERVER_PARAMS = {
#    'api_base': 
}

# URL mappings for web.py
urls = ('/smartapp/index.html', 'index04',
        '/smartapp/index-0.4.html', 'index04',
        '/smartapp/index-0.3.html', 'index03',
        '/smartapp/getcalls', 'get_calls',
        '/smartapp/apicall', 'api_call',
        '/smartapp/smart_manifest.json', 'manifest04',
        '/smartapp/smart_manifest-0.4.json', 'manifest04',
        '/smartapp/smart_manifest-0.3.json', 'manifest03',
        '/smartapp/icon.png', 'icon',
        '/smartapp/runtests', 'run_tests')
        
class icon:
    '''Disseminator for the app icon'''
    def GET(self):
        f = open(APP_PATH + '/smartapp/icon.png', 'r')
        data = f.read()
        f.close()
        web.header('Content-Type', 'image/png')
        return data

class manifest04:
    '''Disseminator for the SMART v0.4 manifest'''
    def GET(self):
        f = open(APP_PATH + '/smartapp/smart_manifest-0.4.json', 'r')
        json = f.read()
        f.close()
        web.header('Content-Type', 'application/json')
        return json
        
class manifest03:
    '''Disseminator for the SMART v0.3 manifest'''
    def GET(self):
        f = open(APP_PATH + '/smartapp/smart_manifest-0.3.json', 'r')
        json = f.read()
        f.close()
        web.header('Content-Type', 'application/json')
        return json

class index04:
    '''Disseminator for the SMART v0.4 tester index page'''
    def GET(self):
        f = open(APP_PATH + '/templates/index-0.4.html', 'r')
        html = f.read()
        f.close()
        return html
        
class index03:
    '''Disseminator for the SMART v0.3 tester index page'''
    def GET(self):
        f = open(APP_PATH + '/templates/index-0.3.html', 'r')
        html = f.read()
        f.close()
        return html

class get_calls:
    def GET(self):
        '''Returns the available python client calls based on the ontology'''
        
        # Load the local copy of the ontology via the SMART client
        try:
            sc = get_smart_client(APP_PATH + '/data/smart.owl')
        except:
            # When the oauth credentials are bad or another execption occurs,
            # perform a manual ontology parsing routine which blocks any
            # consequent SMART client instantiations
            rdf_ontology.parse_ontology(open(APP_PATH + '/data/smart.owl').read())

        # Initialize the output dictionary
        out = {}

        # Iterate over the ontology calls
        for t in rdf_ontology.api_calls:
        
            # Fetch the metadata of the api call
            path = str(t.path)
            method = str(t.method)
            target = str(t.target)
            category = str(t.category)
            
            # Process only GET calls of "record_items" category plus a few specific
            # exceptions by adding them to the dictionary
            if method == "GET" and (category == "record_items" or
                                    path == "/ontology" or
                                    path == "/apps/manifests/" or
                                    path == "/capabilities/"):

                # Build the generic python client call name and use it in the dictionary
                out[target] = {"call_py": get_call(target)}

        # Return the dictionary serialized as "pretty" JSON
        return json.dumps(out, sort_keys=True, indent=4)
        
class api_call:
    def POST(self):
        '''Executes a python client API call identified by its generic name'''
        
        # Get the call name from the HTTP header
        call_name = web.input().call_name
        
        print >> sys.stderr, "calling " + call_name
        
        # Load the local ontology into the SMART client
        smart_client = get_smart_client(APP_PATH + '/data/smart.owl')
        
        # Figure out the SMART model corresponding to the API call
        model = get_model(call_name)
        
        # Get a reference to the conveninence method in the SMART client and execute the call
        method_to_call = getattr(smart_client, call_name)
        r = method_to_call()
        
        # Run the API tests on the result of the call
        messages = getMessages(runTest(model,r.body,r.contentType))
        
        # Encode and return the call and tests result as JSON
        return json.dumps({'body':r.body, 'contentType':r.contentType, 'messages':messages}, sort_keys=True, indent=4)

class run_tests:
    def POST(self):
        '''Executes the appropriate series of tests for a given SMART data model'''
        
        # Get the input data from the HTTP header
        model = web.input().model
        data = web.input().data
        contentType = web.input().content_type
        
        # Run the tests and obtain the failure messages
        messages = getMessages(runTest(model,data,contentType))

        # Return the failure messages encoded as JSON
        return json.dumps(messages, sort_keys=True, indent=4)
        
def get_call(target):
    '''Returns the name of the SMART python client convenience method
    corresponding to the target SMART data model
    
    Expects a valid SMART data model target
    '''
    
    # Local class needed by the call_name method
    class API_Call():
        def __init__ (self, path, method):
            self.path = path
            self.method = method

    # Get all the API calls from the ontology
    r = rdf_ontology.get_api_calls()
    
    # Construct an API_Call object
    call = API_Call(r[target], "GET")
    
    # Obtain and return the call name
    return call_name(call)
    
def get_model(call):
    '''Returns the name of the target SMART data model
    corresponding to the SMART python client convenience method
    
    Expects a valid SMART python client convenience method name
    '''
    
    # Local class needed by the call_name method
    class API_Call():
        def __init__ (self, path, method):
            self.path = path
            self.method = method

    if not rdf_ontology.api_types:
        rdf_ontology.parse_ontology(open(APP_PATH + '/data/smart.owl').read())
            
    # Get all the API calls from the ontology
    r = rdf_ontology.get_api_calls()
    
    # Look through the api calls array until a call with matching convenience method name is found
    for target in r.keys():
        if call == call_name(API_Call(r[target], "GET")):
            return target.replace("http://smartplatforms.org/terms#","")
        
def get_smart_client(ontology = None):
    '''Initializes and returns a new SMART Client
    
    Expects an OAUTH header as a REST parameter
    '''
    smart_oauth_header = web.input().oauth_header
    smart_oauth_header = urllib.unquote(smart_oauth_header)
    oa_params = oauth.parse_header(smart_oauth_header)
    SMART_SERVER_PARAMS['api_base'] = oa_params['smart_container_api_base']
    SMART_SERVER_OAUTH['consumer_key'] = oa_params['smart_app_id']

    oa_params = oauth.parse_header(smart_oauth_header)
    
    resource_tokens={'oauth_token':       oa_params['smart_oauth_token'],
                     'oauth_token_secret':oa_params['smart_oauth_token_secret']}

    ret = SmartClient(SMART_SERVER_OAUTH['consumer_key'], 
                       SMART_SERVER_PARAMS, 
                       SMART_SERVER_OAUTH, 
                       resource_tokens,
                       ontology)
                       
    ret.record_id=oa_params['smart_record_id']
    ret.user_id=oa_params['smart_user_id']
    ret.smart_app_id=oa_params['smart_app_id']
    
    return ret

# Initialize web.py
web.config.debug=False
app = web.application(urls, globals())

if __name__ == "__main__":
    app.run()
else:
    application = app.wsgifunc()