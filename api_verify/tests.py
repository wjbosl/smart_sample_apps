'''Module providing testing functionaly for the SMART API Verifier'''
# Developed by: Nikolai Schwertner
#
# Revision history:
#     2012-02-24 Initial release

# Import some general modules
import os
import unittest
import string
import json
import threading

# ISO 8601 date parser
# Make sure that you match the version of the library with your version
# of Python when you install it (Setup Tools / Easy Install does it incorrectly)
import dateutil.parser

# Enables automated sparql query generation from the ontology
import query_builder

# RDF parsing wrapper from the SMART python client
from smart_client.common.util import parse_rdf

# Global variables for state synchronization accross the test suites
lock = threading.Lock()
data = None
ct = None
currentModel = None

class TestDefault(unittest.TestCase):
    '''Default tests run on unidentified models'''
    
    def testUnknown(self):
        self.fail("Data model does not have an associated test suite")

class TestRDF(unittest.TestCase):
    '''Tests for RDF data parsing and content types'''

    def setUp(self):
        '''General tests setup (parses the RDF string in the global data var)'''
        try:
            self.rdf = parse_rdf(data)
            self.failed = False
        except:
            self.rdf = None
            self.failed = True

    def testValidRDF(self):
        '''Reports the outcome of the RDF parsing'''
        if self.failed:
            self.fail("RDF-XML parsing failed")
        elif not self.rdf:
            self.fail("EMPTY RESULT SET")
    
    def testContentType(self):
        '''Verifies that the content type provided is application/rdf+xml'''
        RDF_MIME = "application/rdf+xml"
        self.assertEquals(ct, RDF_MIME, "HTTP content-type '%s' should be '%s'" % (ct, RDF_MIME))

def testRDF (graph, model):
    # Vars for tracking of the test state
    message = ""

    # Generate the queries
    queries = query_builder.get_queries(model)
    
    for query in queries:
        type = query["type"]
        q = query["query"]
        
        # Negative queries should not return any results
        if type == "negative":
            # Run the query and report any failures
            results = graph.query(q)
            
            # Stingify the results
            myres = []
            for r in results:
                if len (myres) < 3:
                    myres.append(str(r))
            
            # If we get a result (the queries are assumed to be negative),
            # then we fail the test
            if len(myres) > 0 :
                if len(message) == 0:
                    message = "RDF structure check failed\n"
                message += "Got unexpected results (first 3 shown) " + str(myres)
                message += " from the query:\n" + q + "\n"
        
        # The results of select queries should match one of the constraints       
        elif type == "select":       
            # Run the query and report any failures
            results = graph.query(q)
            
            unmatched_results = []

            for r in results:
                matched = False
                
                for c in query["constraints"]:
                    if (str(r[0]).lower(),str(r[1]).lower(),str(r[2]).lower(),str(r[3]).lower(),str(r[4]).lower()) == (c['uri'].lower(), c['code'].lower(), c['identifier'].lower(), c['title'].lower(), c['system'].lower()):
                        matched = True
                        
                if not matched and len (unmatched_results) < 3:
                    unmatched_results.append(" ".join((str(r[0]),str(r[1]),str(r[2]),str(r[3]),str(r[4]))))
            
            if len (unmatched_results) > 0:
                if len(message) == 0:
                    message = "RDF structure check failed\n"
                message += "Got invalid results (first 3 shown) " + str(unmatched_results)
                message += " from the query:\n" + q + "\n"
                    
        # Singular queries test for violations of "no more than 1" restrictions.
        # There should be no duplicates in the result set
        elif type == "singular":
            
            # Run the query and report any failures
            results = graph.query(q)
            
            # Stingify the results
            myres = []
            for r in results:
                myres.append(str(r))
            
            # Find all the duplicates in the result set
            checked = []
            duplicates = []
            for s in myres:
                if s not in checked:
                    checked.append (s)
                elif len(duplicates) < 3:
                    duplicates.append (s)
                  
            # Fail the test when we have duplicates
            if len(duplicates) > 0:
                
                if len(message) == 0:
                    message = "RDF structure check failed\n"
                message += "Got unexpected duplicates (first 3 shown) " + str(duplicates)
                message += " in the results from the query:\n" + q + "\n"
                    
    return message
  
class TestDataModelStructure(unittest.TestCase):
    '''Tests for RDF document structure and content types'''
    
    def setUp(self):
        '''General tests setup (parses the RDF string in the global data var)'''
        try:
            self.rdf = parse_rdf(data)
        except:
            self.rdf = None

    def testStructure(self):
        '''Tests the data model structure with an automatically generated SPARQL queries based on the ontology'''

        if self.rdf:
            # Run the queries against the RDF and get the error message (if any)
            message = testRDF (self.rdf, currentModel)

            # Trigger the fail process if we have failed any of the queries
            if len(message) > 0: self.fail (message)

class TestJSON(unittest.TestCase):
    '''Tests for JSON data parsing and content types'''
    
    def setUp(self):
        '''General tests setup (parses the JSON string in the global data var)'''
        try:
            self.json = json.loads(data)
        except:
            self.json = None

    def testValidJSON(self):
        '''Reports the outcome of the JSON parsing'''
        if not self.json:
            self.fail("JSON parsing failed")

    def testContentType(self):
        '''Verifies that the content type provided is application/json'''
        JSON_MIME = "application/json"
        self.assertEquals(ct, JSON_MIME, "HTTP content-type '%s' should be '%s'" % (ct, JSON_MIME))
         
class TestAllergies(TestRDF):
    '''Tests for Allergies data model'''
    def testStructure2(self):
        '''Tests the data model structure with automatically generated SPARQL queries based on the ontology
        
        This model is a corner case, because it is allowed to confirm to either one of two patterns (Allergy and AllergyExclusion)'''
        if self.rdf:
            # Run the queries against the RDF and get the error messages (if any)
            message1 = testRDF (self.rdf, "Allergy")
            message2 = testRDF (self.rdf, "AllergyExclusion")

            # Trigger the fail process if we have failed any of the queries
            if len(message1) > 0 or len(message2) > 0: self.fail (message1 + message2)

class TestDemographics(TestRDF, TestDataModelStructure):
    '''Tests for the Demographics data model'''
    pass

class TestEncounters(TestRDF, TestDataModelStructure):
    '''Tests for the Encounters data model'''
    pass
    
class TestFulfillments(TestRDF, TestDataModelStructure):
    '''Tests for the Fulfillments data model'''
    pass
    
class TestImmunizations(TestRDF, TestDataModelStructure):
    '''Tests for the Immunizations data model'''
    pass
    
class TestLabResults(TestRDF, TestDataModelStructure):
    '''Tests for the Lab Results data model'''
    pass
    
class TestMedications(TestRDF, TestDataModelStructure):
    '''Tests for the Medications data model'''
    pass
    
class TestProblems(TestRDF, TestDataModelStructure):
    '''Tests for the Problems data model'''
    pass
    
class TestVitalSigns(TestRDF, TestDataModelStructure):
    '''Tests for the Vital Signs data model'''
    
    def testHeight(self):
        '''Tests the height component of the Vital Signs RDF'''
        
        if self.rdf:
        
            # Query for extracting height data from the RDF stream
            q = """
                PREFIX dcterms:<http://purl.org/dc/terms/>
                PREFIX sp:<http://smartplatforms.org/terms#>
                SELECT  ?vital_date ?height ?units
                WHERE {
                   ?v dcterms:date ?vital_date .
                   ?v sp:height ?h .
                   ?h sp:value ?height .
                   ?h sp:unit ?units .
                }
                """
            
            # Run the query
            data = self.rdf.query(q)
            
            for d in data:
                # Store the data in local variables
                vital_date = str(d[0])
                height = str(d[1])
                units = str(d[2])
                
                # Test the date parsing
                try:
                    dateutil.parser.parse(vital_date)
                except ValueError:
                    self.fail("Encountered non-ISO8601 date: " + vital_date)

                # See if the height is a number
                try:
                    float(height)
                except ValueError:
                    self.fail("Could not parse height value: " + height)
                
                # The units should be meters
                if units != 'm':
                    self.fail("Encountered bad units: " + units)
                    
    def testBloodPressure(self):
        '''Tests the blood pressure component of the vital signs RDF'''
        
        if self.rdf:
            
            # Query for extracting of the date and the blood pressure anonymous node label
            q = """
                PREFIX dcterms:<http://purl.org/dc/terms/>
                PREFIX sp:<http://smartplatforms.org/terms#>
                SELECT  ?vital_date ?bloodPressure
                WHERE {
                   ?v dcterms:date ?vital_date .
                   ?v sp:bloodPressure ?bloodPressure .
                }
                """
            
            # Run the query
            data = self.rdf.query(q)
            
            for d in data:
            
                # Get the query results
                vital_date = str(d[0])
                bloodPressure = str(d[1])
                
                # Test the expected date against the ISO 8601 standard
                try:
                    dateutil.parser.parse(vital_date)
                except ValueError:
                    self.fail("Encountered non-ISO8601 date: " + vital_date)
                
                # Construct a query for extracting the specific values of the blood pressure reading
                q = """
                    PREFIX dcterms:<http://purl.org/dc/terms/>
                    PREFIX sp:<http://smartplatforms.org/terms#>
                    SELECT  ?systolic ?diastolic ?units1 ?units2
                    WHERE {
                       _:%s sp:systolic ?s .
                       ?s sp:value ?systolic .
                       ?s sp:unit ?units1 .
                       _:%s sp:diastolic ?d .
                       ?d sp:value ?diastolic .
                       ?d sp:unit ?units2 .
                    }
                    """ % (bloodPressure, bloodPressure)
            
                # Run the query
                data2 = self.rdf.query(q)
                
                for t in data2:
                    # Fetch the query results
                    systolic = str(t[0])
                    diastolic = str(t[1])
                    units1 = str(t[2])
                    units2 = str(t[3])
                    
                    # See if the systolic value is a numeric
                    try:
                        float(systolic)
                    except ValueError:
                        self.fail("Could not parse systolic pressure value: " + systolic)
                        
                    # See if the diastolic value is a numeric
                    try:
                        float(diastolic)
                    except ValueError:
                        self.fail("Could not parse diastolic pressure value: " + diastolic)
                    
                    # Make sure that the units are mmHg
                    if units1 != 'mm[Hg]':
                        self.fail("Encountered bad units: " + units1)
                        
                    if units2 != 'mm[Hg]':
                        self.fail("Encountered bad units: " + units2)
                
class TestOntology(TestRDF):
    '''Tests for the ontology'''
    pass
    
class TestCapabilities(TestJSON):
    '''Tests for the capabilities API'''
    pass
    
class TestManifests(TestJSON):
    '''Tests for the manifests'''
    pass
    
class TestPreferences(unittest.TestCase):
    '''Tests for the Preferences API'''
    
    def testConsistency(self):
        '''Tests if the data is consistent with the content type (when RDF or JSON)'''
        
        # When the content type is application/json, try parsing the data as JSON
        if ct == 'application/json':
            try:
                json.loads(data)
            except:
                self.fail("HTTP content-type is 'application/json' but JSON parsing failed")
            
        # When the content type is application/rdf+xml, try parsing the data as RDF
        if ct == 'application/rdf+xml':
            try:
                parse_rdf(data)
            except:
                self.fail("HTTP content-type is 'application/rdf+xml' but RDF-XML parsing failed")

# Defines the mapping between the content models and the test suites
tests = {'Allergy': TestAllergies,
         'AppManifest': TestManifests,
         'Demographics': TestDemographics,
         'Container': TestCapabilities,
         'Encounter': TestEncounters,
         'Fulfillment': TestFulfillments,
         'Immunization': TestImmunizations,
         'LabResult': TestLabResults,
         'Medication': TestMedications,
         'Ontology': TestOntology,
         'Problem': TestProblems,
         'UserPreferences': TestPreferences,
         'VitalSigns': TestVitalSigns}

def runTest(model, testData, contentType=None):
    '''Runs the test suite applicable for a model'''
    
    # The lock assures that any concurrent threads are synchronized so that
    # they don't interfere with each other through the global variables
    with lock:
    
        # Get hold of the global variables
        global data
        global ct
        global currentModel
        
        # Assign the input data to the globals
        data = testData
        ct = contentType
        currentModel = model
        
        # Load the test from the applicable test suite
        if model in tests.keys():
            alltests = unittest.TestLoader().loadTestsFromTestCase(tests[model])
        else:
            alltests = unittest.TestLoader().loadTestsFromTestCase(TestDefault)
        
        # Run the tests
        results = unittest.TextTestRunner(stream = open(os.devnull, 'w')).run(alltests)
        
        # Return the test results
        return results
    
def getMessages (results):
    '''Returns an array of strings representing the custom failure messages from the results'''
    
    res = []
    
    # Add all the failure messages to the array
    for e in results.failures:
        res.append ("[" + e[0]._testMethodName + "] " + getShortMessage(e[1]))
        
    # And then add all the error messages
    for e in results.errors:
        res.append ("[" + e[0]._testMethodName + "] " + e[1])

    return res

def getShortMessage (message):
    '''Returns the custom message portion of a unittest failure message'''
    
    s = message.split("AssertionError: ")
    return s[1]
