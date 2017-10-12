#! /usr/bin/python

"""
generic to task-juggler extraction script

This script queries generic, and generates a task-juggler input file in order to generate a gant-chart.
"""

import logging,tempfile,subprocess,datetime,icalendar,shutil,os
from collections import OrderedDict

DEFAULT_LOGLEVEL = 'warning'
DEFAULT_OUTPUT = 'export.tjp'

TAB = ' ' * 4

DEBUG = False

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def set_logging_level(loglevel):
    '''
    Set the logging level

    Args:
        loglevel String representation of the loglevel
    '''
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.getLogger().setLevel(numeric_level)
    
def to_tj3time(dt):
    """
    Convert python date or datetime object to TJ3 format
    
    """
    return dt.isoformat().replace("T", "-").split(".")[0].split("+")[0]

def to_tj3interval(start, end):
    return "%s - %s" % (to_tj3time(start), to_tj3time(end))

TJP_NUM_ID_PREFIX = "tjp_numid_"
TJP_DASH_PREFIX = "__DASH__"
TJP_SPACE_PREFIX = "__SPACE__"

def to_identifier(key):
    '''
    Convert given key to identifier, interpretable by TaskJuggler as a task-identifier

    Args:
        key (str): Key to be converted

    Returns:
        str: Valid task-identifier based on given key
    '''
    if is_number(key):
        key = TJP_NUM_ID_PREFIX+str(key)
    key = key.replace('-', TJP_DASH_PREFIX).replace(" ", TJP_SPACE_PREFIX)
    return key

def from_identifier(key):
    if TJP_NUM_ID_PREFIX in key:
        return int(key.replace(TJP_NUM_ID_PREFIX, ""))
    return key.replace(TJP_DASH_PREFIX, "-").replace(TJP_SPACE_PREFIX, " ")

class JugglerTaskProperty(object):
    '''Class for a property of a Task Juggler'''

    DEFAULT_NAME = 'property name'
    DEFAULT_VALUE = 'not initialized'
    PREFIX = ''
    SUFFIX = ''
    TEMPLATE = TAB + '{prop} {value}\n'
    VALUE_TEMPLATE = '{prefix}{value}{suffix}'
    LOG_STRING = "Default TaskProperty"


    def __init__(self, issue=None):
        '''
        Initialize task juggler property

        Args:
            issue (class): The generic issue to load from
            value (object): Value of the property
        '''
        logging.debug('Create %s', self.LOG_STRING)
        self.name = self.DEFAULT_NAME
        self.set_value(self.DEFAULT_VALUE)
        self.empty = False
        self.parent = None
        self.load_default_properties(issue)

        if issue:
            if self.load_from_issue(issue) is False:
                self.empty = True

    def load_default_properties(self, issue = None):
        pass

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
        
    def get_id(self):
        return ""
        
    def get_hash(self):
        return self.get_name() + repr(self.get_value())

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
        if self.value == self.DEFAULT_VALUE: return ""
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
            # TODO: list support (like allocate multiple) (copy from taskdepends)
            # TODO: identifier conversion support?
            return self.TEMPLATE.format(prop=self.get_name(),
                                        value=self.VALUE_TEMPLATE.format(prefix=self.PREFIX,
                                                                         value=self.get_value(),
                                                                         suffix=self.SUFFIX))
        return ''

class JugglerTaskAllocate(JugglerTaskProperty):
    '''Class for the allocate (assignee) of a juggler task'''

    DEFAULT_NAME = 'allocate'
    DEFAULT_VALUE = 'not initialized'

    def load_from_issue(self, issue = None):
        '''
        Load the object with data from a generic issue

        Args:
            issue (class): The generic issue to load from
        '''
        self.set_value(self.DEFAULT_VALUE)
        if not issue is None:
            self.set_value(issue) # TODO: this may be list or primitive

class JugglerTaskPriority(JugglerTaskProperty):
    '''Class for task priority'''
    LOG_STRING = "JugglerTaskPriority"
    DEFAULT_NAME = "priority"
    DEFAULT_VALUE = 1000
    
    def get_hash(self):
        return self.get_name()

class JugglerTaskStart(JugglerTaskProperty):
    LOG_STRING = "JugglerTaskStart"
    DEFAULT_NAME = "start"
    DEFAULT_VALUE = ""
    
    def set_value(self, dt):
        if not dt: 
            self.value = ""
            return
        if not isinstance(dt, datetime.datetime):
            raise ValueError("Task start value should be datetime object")
        self.value = dt
    
    def get_value(self):
        # TODO: fix API
        # WARNING: get_value returns tjp value
        if not self.value:
            return ""
        return to_tj3time(self.value)
        
    def get_hash(self):
        return self.get_name()

class JugglerTaskEffort(JugglerTaskProperty):
    '''Class for the effort (estimate) of a juggler task'''

    #For converting the seconds (generic) to days
    UNIT = 'h'

    DEFAULT_NAME = 'effort'
    MINIMAL_VALUE = 1 # TODO: should be project resolution, add check
    DEFAULT_VALUE = -1 
    SUFFIX = UNIT

    def load_default_properties(self, issue = None):
        self.SUFFIX = self.UNIT

    def load_from_issue(self, issue):
        '''
        Load the object with data from a generic issue

        Args:
            issue (class): The generic issue to load from
        '''
        if issue: self.set_value(issue)
        else: self.set_value(self.DEFAULT_VALUE)
    def set_value(self, value):
        '''
        Set the value for effort. Will convert whatever number to integer.
        
        Default class unit is 'days'. Can be overrided by setting "UNIT" global class attribute
        '''
        self.value = int(value)
    def get_hash(self):
        return self.get_name()
    def validate(self, task, tasks):
        '''
        Validate (and correct) the current task property

        Args:
            task (JugglerTask): Task to which the property belongs
            tasks (list):       List of JugglerTask's to which the current task belongs. Will be used to
                                verify relations to other tasks.
        '''
        pass
        # if self.get_value() < self.MINIMAL_VALUE:
        #     logging.warning('Estimate %s%s too low for %s, assuming %s%s', self.get_value(), self.UNIT, task.key, self.MINIMAL_VALUE, self.UNIT)
        #     self.set_value(self.MINIMAL_VALUE)

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
        raise NotImplementedError("load_from_issue is not implemented for this depend")
        # TODO: remove these - are for jira
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
        # TODO: add support for nested tasks with self.parent
        for val in list(self.get_value()):
             if val not in [tsk.get_id() for tsk in tasks]:
                 logging.warning('Removing link to %s for %s, as not within scope', val, task.get_id())
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
                                                     value=to_identifier(val),
                                                     suffix=self.SUFFIX)
            return self.TEMPLATE.format(prop=self.get_name(),
                                        value=valstr)
        return ''

# class NonEmptyObject(object):
#     def __init__(self):
#         self.empty = False
#     def __bool__(self):
#         return not self.empty
#     __nonzero__=__bool__
    

class JugglerCompoundKeyword(object):

    '''Class for a general compound object in TJ syntax'''

    COMMENTS_HEADER = ""
    LOG_STRING = "DefaultKeyword"
    DEFAULT_KEYWORD = 'unknown_keyword'
    DEFAULT_ID = "" # id may be empty for some keywords
    DEFAULT_SUMMARY = '' # no summary is possible everywhere
    TEMPLATE = '''{header}\n{keyword} {id}'''
    ENCLOSED_BLOCK = True

    def __init__(self, issue=None):
        logging.debug('Create %s', self.LOG_STRING)
        self.empty = False
        self.parent = None
        self.keyword = self.DEFAULT_KEYWORD
        self.id = self.DEFAULT_ID
        self.summary = self.DEFAULT_SUMMARY
        self.option2 = ""
        self.properties = OrderedDict()
        self.load_default_properties(issue)

        if issue:
            if self.load_from_issue(issue) is False:
                self.empty = True
    
    def load_from_issue(self, issue):
        '''
        Load the object with data from a generic issue

        Args:
            issue (class): The generic issue to load from
        '''
        pass
    
    def load_default_properties(self, issue = None):
        pass
    
    def get_name(self):
        return self.keyword
        
    def get_id(self):
        return self.id
    
    def get_hash(self):
        """Used to generate unique hash. 
        
        If set_property should replace this (only single property of this type is supported) - 
            - the hash should only return the keyword
        
        By default, multiple compound properties are allowed.
        """
        return self.get_name() + repr(self.get_id())

    def set_property(self, prop):
        if prop: 
            self.properties[prop.get_hash()] = prop
            prop.parent = self # TODO: control un-set?, GC?
    
    def set_id(self, id):
        self.id = id
    
    def decode(self):
        return self.option2
    
    def walk(self, cls, ls = None):
        if ls is None: ls = []
        for key, item in self.properties.items():
            if isinstance(item, JugglerCompoundKeyword):
                ls = item.walk(cls, ls)
            if isinstance(item, cls):
                ls.append(item)
        return ls
    
    def __str__(self):
        if self.empty: return ""
        out = self.TEMPLATE.format(header=self.COMMENTS_HEADER,keyword=self.keyword, id=to_identifier(self.id))
        if self.summary:
            out += ' "%s"' % self.summary.replace('\"', '\\\"')
        if self.option2:
            out += ' %s ' % self.option2
        if self.properties and self.ENCLOSED_BLOCK: out += " {\n"
        for prop in self.properties:
            out += str(self.properties[prop])
        if self.properties and self.ENCLOSED_BLOCK: out += "\n}"
        return out

class JugglerSimpleProperty(JugglerCompoundKeyword):
    """By default only one simple property is allowed."""
    LOG_STRING = "Default Simple Property"
    DEFAULT_NAME = 'unknown_property'
    DEFAULT_VALUE = ''
    
    def load_default_properties(self, issue = None):
        self.keyword = self.DEFAULT_NAME
        self.set_value(self.DEFAULT_VALUE)
    
    def load_from_issue(self, value):
        self.set_value(value)
        
    def get_name(self):
        return self.keyword
    
    def get_hash(self):
        return self.get_name()
    
    def decode(self):
        return self.id
    
    def get_value(self):
        return self.id
    
    def set_value(self, val):
        if val or val == 0: self.id = repr(val).replace("'",'"')
    
class JugglerTimezone(JugglerSimpleProperty):
    '''
    Sets the project timezone.
    Default value is UTC.
    
    Supports all tzdata values, see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    or https://stackoverflow.com/q/13866926
    '''
    DEFAULT_NAME = 'timezone'
    DEFAULT_VALUE = 'UTC'
    # DEFAULT_VALUE = 'Europe/Dublin'
    
    # TODO: checks!

class JugglerOutputdir(JugglerSimpleProperty):
    LOG_STRING = "outputdir property"
    DEFAULT_NAME = 'outputdir'
    DEFAULT_VALUE = 'REPORT'
    # TODO HERE: need to create the outputdir folder for this to execute!

class JugglerIcalreport(JugglerSimpleProperty):
    LOG_STRING = "icalreport property"
    DEFAULT_NAME = 'icalreport'
    DEFAULT_VALUE = 'calendar'

class JugglerResource(JugglerCompoundKeyword):
    DEFAULT_KEYWORD = "resource"
    DEFAULT_ID = "me"
    DEFAULT_SUMMARY = "Default Resource"

class JugglerTask(JugglerCompoundKeyword):

    '''Class for a task for Task-Juggler'''

    LOG_STRING = "JugglerTask"
    DEFAULT_KEYWORD = 'task'
    DEFAULT_ID = "unknown_task"
    DEFAULT_SUMMARY = 'Task is not initialized'
    
    def load_default_properties(self, issue = None):
        if not issue:
            self.set_property(JugglerTaskAllocate("me"))
            self.set_property(JugglerTaskEffort(1))
        else:
            self.set_property(JugglerTaskAllocate(issue))
            self.set_property(JugglerTaskEffort(issue))
            self.set_property(JugglerTaskDepends(issue))
        
    def load_from_issue(self, issue):
        '''
        Load the object with data from a generic issue

        Args:
            issue (?): The generic issue to load from
        '''
        self.load_default_properties(issue)
    
    def validate(self, tasks):
        '''
        Validate (and correct) the current task

        Args:
            tasks (list): List of JugglerTask's to which the current task belongs. Will be used to
                          verify relations to other tasks.
        '''
        if self.id == self.DEFAULT_ID:
            logging.error('Found a task which is not initialized')

        for prop in self.properties:
            self.properties[prop].validate(self, tasks)

    # def __str__(self):
    #     '''
    #     Convert task object to the task juggler syntax

    #     Returns:
    #         str: String representation of the task in juggler syntax
    #     '''
    #     props = ''
    #     for prop in self.properties:
    #         props += str(self.properties[prop])
    #     return self.TEMPLATE.format(id=to_identifier(self.key),
    #                                 key=self.key,
    #                                 description=self.summary.replace('\"', '\\\"'),
    #                                 props=props)

class JugglerTimesheet():
    pass

class JugglerBooking(JugglerCompoundKeyword):
    LOG_STRING = "JugglerBooking"
    DEFAULT_KEYWORD = "booking"
    DEFAULT_ID = "me" # resource
    
    def load_default_properties(self, issue = None):
        self.start = None
        self.end = None
    
    def set_resource(self, res):
        self.set_id(res)
    
    def set_interval(self, start, end):
        self.start = start
        self.end = end
        self.option2 = to_tj3interval(self.start, self.end)
    
    def decode(self):
        return [self.start, self.end]
    
    def load_from_issue(self, issue = None):
        start = issue["start"]
        end = issue["end"]
        self.set_interval(start, end)
        self.set_resource(issue["resource"])

class JugglerProject(JugglerCompoundKeyword):
    
    '''Template for TaskJuggler project'''
    
    LOG_STRING = "JugglerProject"
    DEFAULT_KEYWORD = 'project'
    DEFAULT_ID = "default" # id may be empty for some keywords
    DEFAULT_SUMMARY = 'Default Project' # no summary is possible everywhere
    
    def load_default_properties(self, issue = None):
        self.set_property(JugglerTimezone())
        self.set_property(JugglerOutputdir())
        self.set_interval()
    
    def set_interval(self, start = datetime.datetime.now().replace(microsecond=0,second=0,minute=0), end = datetime.datetime(2035, 1, 1)):
        self.option2 = to_tj3interval(start, end)
        

class JugglerSource(JugglerCompoundKeyword):
    """
    The entire project skeleton
    
    Sets reports and folders for use with parser
    
    Must be extended with load_from_issue(self,issue) appending tasks 
    """
    
    LOG_STRING = "JugglerSource"
    DEFAULT_KEYWORD = ''
    DEFAULT_ID = ''
    COMMENTS_HEADER = '''
    // TaskJuggler 3 source
    // generated by python-juggler (c) 2017 Andrew Gryaznov and others
    // https://github.com/grandrew/taskjuggler-python
    '''
    ENCLOSED_BLOCK = False
    
    def load_default_properties(self, issue = None):
        self.set_property(JugglerProject())
        self.set_property(JugglerResource())
        self.set_property(JugglerIcalreport())
        
class GenericJuggler(object):

    '''Class for task-juggling generic results'''
    
    src = None
    
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
        
    def add_task(self, task):
        '''
        Add task to current project
        
        Args:
            task (JugglerTask): a task to add
        '''
        if not self.src:
            self.juggle()
        self.src.set_property(task)

    def load_issues_incremetal(self):
        if self.loaded: return []
        self.loaded = True
        return self.load_issues()
    
    def create_task_instance(self, issue):
        return JugglerTask(issue)

    def load_issues_from_generic(self):
        '''
        Load issues from generic

        Returns:
            list: A list of dicts containing the generic tickets
        '''
        tasks = []
        busy = True
        self.loaded = False
        self.issue_count = 0
        
        while busy:
            try:
                issues = self.load_issues_incremetal()
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
                logging.debug('Retrieved %s', repr(issue))
                tasks.append(self.create_task_instance(issue))

        self.validate_tasks(tasks)

        return tasks
    
    def create_jugglersource_instance(self):
        return JugglerSource()
        
    def juggle(self):
        """
        Export the loaded issues onto the JuggleSource structure
        """
        issues = self.load_issues_from_generic()
        if not issues:
            # return None
            issues = []
        self.src = self.create_jugglersource_instance()
        for issue in issues:
            self.src.set_property(issue)
        return self.src

    def write_file(self, output=None):
        '''
        Query generic and generate task-juggler output from given issues

        Args:
            output (str): Name of output file, for task-juggler
        '''
        
        if not self.src:
            self.juggle()
            
        s = str(self.src)
        
        if output and isinstance(output, str):
            with open(output, 'w') as out:
                out.write(s)
        elif output and isinstance(output, file):
            output.write(s)
        # else:
        #     raise ValueError("output should be a filename string or a file handler")
        return s
    
    def read_ical_result(self, icalfile):
        tasks = self.src.walk(JugglerTask)
        cal = icalendar.Calendar.from_ical(file(icalfile).read())
        for ev in cal.walk('VEVENT'): # pylint:disable=no-member
            start_date = ev.decoded("DTSTART")
            end_date = ev.decoded("DTEND")
            id = from_identifier(ev.decoded("UID").split("-")[1])
            for t in tasks:
                if t.id == id:
                    # logging.info("Testing %s" % str(t))
                    # logging.info("Got %s" % repr(t.walk(JugglerTaskAllocate)))
                    
                    # ical does not support resource allocation reporting
                    # so we do not support multiple resource here
                    # and we don't support them yet anyways
                    t.set_property(JugglerBooking({
                        "resource":t.walk(JugglerTaskAllocate)[0].get_value(),
                        "start": start_date,
                        "end": end_date
                        }))
    
    def run(self, outfolder=None, infile=None):
        '''
        Run the taskjuggler task

        Args:
            output (str): Name of output file, for task-juggler
        '''
        if not self.src:
            self.juggle()
            
        if outfolder is None:
            outfolder = tempfile.mkdtemp("TJP")
        self.outfolder = outfolder
        
        if infile is None:
            infile = tempfile.mkstemp(".tjp")[1]
        self.infile = infile
        
        reportdir = self.src.walk(JugglerOutputdir)
        orig_rep = reportdir[0].get_value()
        reportdir[0].set_value(outfolder)
        
        ical_report_name = "calendar_out"
        ical_report_path = os.path.join(outfolder, ical_report_name)
        icalreport = self.src.walk(JugglerIcalreport)
        orig_cal = icalreport[0].get_value()
        icalreport[0].set_value(ical_report_name)
        
        self.write_file(infile)
        
        logging.debug("Running from %s to out %s" % (self.infile, self.outfolder))
        
        subprocess.call(["/usr/bin/env", "tj3", infile])
        
        self.read_ical_result(ical_report_path+".ics")
        
        icalreport[0].set_value(orig_cal)
        reportdir[0].set_value(orig_rep)
        
        if DEBUG or logging.getLogger().getEffectiveLevel() >= logging.DEBUG: return
        shutil.rmtree(self.outfolder)
        os.remove(self.infile)
        
        # TODO HERE: load the ical file back to the actual tree (no tree support yet?)
        
    def clean(self):
        "clean after running"
        if DEBUG or logging.getLogger().getEffectiveLevel() >= logging.DEBUG: return
        try: shutil.rmtree(self.outfolder)
        except:  pass
        try: os.remove(self.infile)
        except: pass
    
    def walk(self, cls):
        if not self.src:
            self.juggle()
        return self.src.walk(cls)
    
    def __inter__(self):
        "provide dict(j) method to generate dictionary structure for tasks"
        raise NotImplementedError
    
    def __del__(self):
        self.clean()


