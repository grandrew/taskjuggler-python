#! /usr/bin/python3

"""
generic to task-juggler extraction script

This script queries generic, and generates a task-juggler input file in order to generate a gant-chart.
"""

import logging,tempfile,subprocess

DEFAULT_LOGLEVEL = 'warning'
DEFAULT_OUTPUT = 'export.tjp'

TAB = ' ' * 4

def set_logging_level(loglevel):
    '''
    Set the logging level

    Args:
        loglevel String representation of the loglevel
    '''
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

def to_identifier(key):
    '''
    Convert given key to identifier, interpretable by TaskJuggler as a task-identifier

    Args:
        key (str): Key to be converted

    Returns:
        str: Valid task-identifier based on given key
    '''
    return key.replace('-', '_')

class JugglerTaskProperty(object):
    '''Class for a property of a Task Juggler'''

    DEFAULT_NAME = 'property name'
    DEFAULT_VALUE = 'not initialized'
    PREFIX = ''
    SUFFIX = ''
    TEMPLATE = TAB + '{prop} {value}\n'
    VALUE_TEMPLATE = '{prefix}{value}{suffix}'


    def __init__(self, issue=None):
        '''
        Initialize task juggler property

        Args:
            issue (class): The generic issue to load from
            value (object): Value of the property
        '''
        self.name = self.DEFAULT_NAME
        self.set_value(self.DEFAULT_VALUE)

        if issue:
            self.load_from_issue(issue)

    def load_from_issue(self, issue):
        '''
        Load the object with data from a generic issue

        Args:
            issue (class): The generic issue to load from
        '''
        pass

    def get_name(self):
        '''
        Get name for task juggler property

        Returns:
            str: Name of the task juggler property
        '''
        return self.name

    def set_value(self, value):
        '''
        Set value for task juggler property

        Args:
            value (object): New value of the property
        '''
        self.value = value

    def append_value(self, value):
        '''
        Append value for task juggler property

        Args:
            value (object): Value to append to the property
        '''
        self.value.append(value)

    def get_value(self):
        '''
        Get value for task juggler property

        Returns:
            str: Value of the task juggler property
        '''
        return self.value

    def validate(self, task, tasks):
        '''
        Validate (and correct) the current task property

        Args:
            task (JugglerTask): Task to which the property belongs
            tasks (list):       List of JugglerTask's to which the current task belongs. Will be used to
                                verify relations to other tasks.
        '''
        pass

    def __str__(self):
        '''
        Convert task property object to the task juggler syntax

        Returns:
            str: String representation of the task property in juggler syntax
        '''

        if self.get_value():
            return self.TEMPLATE.format(prop=self.get_name(),
                                        value=self.VALUE_TEMPLATE.format(prefix=self.PREFIX,
                                                                         value=self.get_value(),
                                                                         suffix=self.SUFFIX))
        return ''


    

class JugglerTaskAllocate(JugglerTaskProperty):
    '''Class for the allocate (assignee) of a juggler task'''

    DEFAULT_NAME = 'allocate'
    DEFAULT_VALUE = 'not assigned'

    def load_from_issue(self, issue):
        '''
        Load the object with data from a generic issue

        Args:
            issue (class): The generic issue to load from
        '''
        self.set_value(self.DEFAULT_VALUE)
        if hasattr(issue.fields, 'assignee'):
            self.set_value(issue.fields.assignee.name)

class JugglerTaskEffort(JugglerTaskProperty):
    '''Class for the effort (estimate) of a juggler task'''

    #For converting the seconds (generic) to days
    UNIT = 'd'
    FACTOR = 8.0 * 60 * 60

    DEFAULT_NAME = 'effort'
    MINIMAL_VALUE = 1.0 / 8
    DEFAULT_VALUE = MINIMAL_VALUE
    SUFFIX = UNIT

    def load_from_issue(self, issue):
        '''
        Load the object with data from a generic issue

        Args:
            issue (class): The generic issue to load from
        '''
        self.set_value(self.DEFAULT_VALUE)
        if hasattr(issue.fields, 'aggregatetimeoriginalestimate') and issue.fields.aggregatetimeoriginalestimate:
            val = issue.fields.aggregatetimeoriginalestimate
            self.set_value(val / self.FACTOR)
        else:
            logging.warning('No estimate found for %s, assuming %s%s', issue.key, self.DEFAULT_VALUE, self.UNIT)

    def validate(self, task, tasks):
        '''
        Validate (and correct) the current task property

        Args:
            task (JugglerTask): Task to which the property belongs
            tasks (list):       List of JugglerTask's to which the current task belongs. Will be used to
                                verify relations to other tasks.
        '''
        if self.get_value() < self.MINIMAL_VALUE:
            logging.warning('Estimate %s%s too low for %s, assuming %s%s', self.get_value(), self.UNIT, task.key, self.MINIMAL_VALUE, self.UNIT)
            self.set_value(self.MINIMAL_VALUE)

class JugglerTaskDepends(JugglerTaskProperty):
    '''Class for the effort (estimate) of a juggler task'''

    DEFAULT_NAME = 'depends'
    DEFAULT_VALUE = []
    PREFIX = '!'

    def set_value(self, value):
        '''
        Set value for task juggler property (deep copy)

        Args:
            value (object): New value of the property
        '''
        self.value = list(value)

    def load_from_issue(self, issue):
        '''
        Load the object with data from a generic issue

        Args:
            issue (class): The generic issue to load from
        '''
        self.set_value(self.DEFAULT_VALUE)
        if hasattr(issue.fields, 'issuelinks'):
            for link in issue.fields.issuelinks:
                if hasattr(link, 'inwardIssue') and link.type.name == 'Blocker':
                    self.append_value(to_identifier(link.inwardIssue.key))

    def validate(self, task, tasks):
        '''
        Validate (and correct) the current task property

        Args:
            task (JugglerTask): Task to which the property belongs
            tasks (list):       List of JugglerTask's to which the current task belongs. Will be used to
                                verify relations to other tasks.
        '''
        for val in self.get_value():
            if val not in [to_identifier(tsk.key) for tsk in tasks]:
                logging.warning('Removing link to %s for %s, as not within scope', val, task.key)
                self.value.remove(val)

    def __str__(self):
        '''
        Convert task property object to the task juggler syntax

        Returns:
            str: String representation of the task property in juggler syntax
        '''

        if self.get_value():
            valstr = ''
            for val in self.get_value():
                if valstr:
                    valstr += ', '
                valstr += self.VALUE_TEMPLATE.format(prefix=self.PREFIX,
                                                     value=val,
                                                     suffix=self.SUFFIX)
            return self.TEMPLATE.format(prop=self.get_name(),
                                        value=valstr)
        return ''

class JugglerCompoundKeyword(object):

    '''Class for a general compound object in TJ syntax'''

    LOG_STRING = "DefaultKeyword"
    DEFAULT_KEYWORD = 'unknown_keyword'
    DEFAULT_ID = "" # ID may be empty for some keywords
    DEFAULT_SUMMARY = '' # no summary is possible everywhere
    TEMPLATE = '''\n{keyword} {id}'''

    def __init__(self, issue=None):
        logging.info('Create %s', self.LOG_STRING)

        self.keyword = self.DEFAULT_KEYWORD
        self.ID = self.DEFAULT_ID
        self.summary = self.DEFAULT_SUMMARY
        self.properties = {}
        self.load_default_properties()

        if issue:
            self.load_from_issue(issue)
        
        self.process_values()
            
    def load_from_issue(self, issue):
        '''
        Load the object with data from a generic issue

        Args:
            issue (class): The generic issue to load from
        '''
        pass
    
    def load_default_properties(self):
        pass
    
    def process_values(self):
        pass

    def append_property(self, prop):
        self.properties[prop.get_name()] = prop
    
    def __str__(self):
        out = self.TEMPLATE.format(keyword=self.keyword, id=self.ID)
        if self.summary:
            out += ' "%s"' % self.summary.replace('\"', '\\\"')
        if self.properties: out += " {\n"
        for prop in self.properties:
            out += str(self.properties[prop])
        if self.properties: out += "\n}"
        return out

class JugglerSimpleProperty(JugglerCompoundKeyword):
    DEFAULT_NAME = 'unknown_property'
    DEFAULT_VALUE = ''
    
    def load_default_properties(self):
        self.keyword = self.DEFAULT_NAME
        self.set_value(self.DEFAULT_VALUE)
    
    def load_from_issue(self, value):
        self.set_value(value)
        
    def get_name(self):
        return self.keyword
    
    def get_value(self):
        return self.ID
    
    def set_value(self, val):
        if val or val == 0: self.ID = repr(val).replace("'",'"')
    
class JugglerTimezone(JugglerSimpleProperty):
    DEFAULT_NAME = 'timezone'
    DEFAULT_VALUE = 'Europe/Dublin'
    

class JugglerOutputdir(JugglerSimpleProperty):
    DEFAULT_NAME = 'outputdir'
    DEFAULT_VALUE = 'REPORT'

class JugglerTask(JugglerCompoundKeyword):

    '''Class for a task for Task-Juggler'''

    LOG_STRING = "JugglerTask"
    DEFAULT_KEY = 'NOT_INITIALIZED'
    DEFAULT_SUMMARY = 'Task is not initialized'

    def load_from_issue(self, issue):
        '''
        Load the object with data from a generic issue

        Args:
            issue (class): The generic issue to load from
        '''
        self.key = issue.key
        self.summary = issue.fields.summary.replace('\"', '\\\"')
        self.properties['allocate'] = JugglerTaskAllocate(issue)
        self.properties['effort'] = JugglerTaskEffort(issue)
        self.properties['depends'] = JugglerTaskDepends(issue)

    def validate(self, tasks):
        '''
        Validate (and correct) the current task

        Args:
            tasks (list): List of JugglerTask's to which the current task belongs. Will be used to
                          verify relations to other tasks.
        '''
        if self.key == self.DEFAULT_KEY:
            logging.error('Found a task which is not initialized')

        for prop in self.properties:
            self.properties[prop].validate(self, tasks)

    def __str__(self):
        '''
        Convert task object to the task juggler syntax

        Returns:
            str: String representation of the task in juggler syntax
        '''
        props = ''
        for prop in self.properties:
            props += str(self.properties[prop])
        return self.TEMPLATE.format(id=to_identifier(self.key),
                                    key=self.key,
                                    description=self.summary.replace('\"', '\\\"'),
                                    props=props)

class JugglerTimesheet():
    pass

class JugglerBooking(JugglerTaskProperty):
    pass

class JugglerProject(JugglerCompoundKeyword):
    
    '''Template for TaskJuggler project'''
    
    LOG_STRING = "JugglerProject"
    DEFAULT_KEYWORD = 'project'
    DEFAULT_ID = "default" # ID may be empty for some keywords
    DEFAULT_SUMMARY = '' # no summary is possible everywhere
    
    def load_default_properties(self):
        self.append_property(JugglerTimezone())
        self.append_property(JugglerOutputdir())

class JugglerSource(object):
    """
    The entire project skeleton
    
    Sets reports and folders for use with parser
    """
    
    DEFAULT_KEY = 'NOT_INITIALIZED'
    DEFAULT_SUMMARY = 'Project is not initialized'
    TEMPLATE = '''
    // TaskJuggler 3 source
    // generated by python-juggler (c) 2017 Andrew Gryaznov
    // https://github.com/grandrew/taskjuggler-python
    
    {project}
    
    {tasks}
    
    icalreport "Calendar"
    
'''
    def __init__(self):
        logging.info('Create JugglerSource')

        self.key = self.DEFAULT_KEY
        self.summary = self.DEFAULT_SUMMARY
        self.tasks = {}
        self.project = JugglerProject()
    
    def __str__(self):
        '''
        Convert source object to the task juggler syntax

        Returns:
            str: String representation of the task in juggler syntax
        '''
        tasks = ''
        for task in self.tasks:
            tasks += str(self.tasks[task])
        return self.TEMPLATE.format(tasks=tasks,project=str(self.project))

class GenericJuggler(object):

    '''Class for task-juggling generic results'''

    def __init__(self):
        '''
        Construct a generic juggler object

        Args:
            none
        '''

        logging.info('generic load')

    def set_query(self, query):
        '''
        Set the query for the generic juggler object

        Args:
            query (str): The Query to run on generic server
        '''

        logging.info('Query: %s', query)
        self.query = query
        self.issue_count = 0

    @staticmethod
    def validate_tasks(tasks):
        '''
        Validate (and correct) tasks

        Args:
            tasks (list): List of JugglerTask's to validate
        '''
        for task in tasks:
            task.validate(tasks)

    def load_issues(self):
        raise NotImplementedError

    def load_issues_from_generic(self):
        '''
        Load issues from generic

        Returns:
            list: A list of dicts containing the generic tickets
        '''
        tasks = []
        busy = True
        while busy:
            try:
                issues = self.load_issues()
            except NotImplementedError:
                logging.error('Loading Issues is not implemented in upstream library')
                return None
                
            except:
                logging.error('Could not get issue')
                return None

            if len(issues) <= 0:
                busy = False

            self.issue_count += len(issues)

            for issue in issues:
                logging.debug('Retrieved %s: %s', issue.key, issue.fields.summary)
                tasks.append(JugglerTask(issue))

        self.validate_tasks(tasks)

        return tasks

    def write_file(self, output=None, reportfolder=None):
        '''
        Query generic and generate task-juggler output from given issues

        Args:
            output (str): Name of output file, for task-juggler
        '''
        if output is None:
            output = tempfile.mkstemp()
        self.infile = output
        
        # TODO HERE: set report folder!
        
        issues = self.load_issues_from_generic()
        if not issues:
            return None
        if output:
            with open(output, 'w') as out:
                for issue in issues:
                    out.write(str(issue))
        return issues
        
    def run(self, outfolder=None, infile=None):
        '''
        Run the taskjuggler task

        Args:
            output (str): Name of output file, for task-juggler
        '''
        if outfolder is None:
            outfolder = tempfile.mkdtemp()
        self.outfolder = outfolder
        if infile is None:
            infile = self.infile
        subprocess.call(["/usr/bin/env", "tj3", self.infile])
        
    def juggle(self):
        '''
        Run the juggler with default settings

        Args:
            output (str): Name of output file, for task-juggler
            
        Returns:
            str: taskjuggler output folder location
        '''
        self.load_issues_from_generic()
        self.write_file()
        self.run()
        return self.outfolder
        
    def clean(self):
        "clean after running"
        raise NotImplementedError
    
    def __del__(self):
        self.clean()


