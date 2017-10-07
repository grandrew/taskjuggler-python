#! /usr/bin/python3

"""
Jira to task-juggler extraction script

This script queries Jira, and generates a task-juggler input file in order to generate a gant-chart.
"""

from getpass import getpass
import argparse
import logging
from jira import JIRA, JIRAError

DEFAULT_LOGLEVEL = 'warning'
DEFAULT_JIRA_URL = 'https://jira.melexis.com/jira'
DEFAULT_JIRA_USER = 'swcc'
DEFAULT_JIRA_QUERY = 'project = X AND fixVersion = Y'
DEFAULT_OUTPUT = 'jira_export.tjp'

JIRA_PAGE_SIZE = 50

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


    def __init__(self, jira_issue=None):
        '''
        Initialize task juggler property

        Args:
            jira_issue (class): The Jira issue to load from
            value (object): Value of the property
        '''
        self.name = self.DEFAULT_NAME
        self.set_value(self.DEFAULT_VALUE)

        if jira_issue:
            self.load_from_jira_issue(jira_issue)

    def load_from_jira_issue(self, jira_issue):
        '''
        Load the object with data from a Jira issue

        Args:
            jira_issue (class): The Jira issue to load from
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

    def load_from_jira_issue(self, jira_issue):
        '''
        Load the object with data from a Jira issue

        Args:
            jira_issue (class): The Jira issue to load from
        '''
        self.set_value(self.DEFAULT_VALUE)
        if hasattr(jira_issue.fields, 'assignee'):
            self.set_value(jira_issue.fields.assignee.name)

class JugglerTaskEffort(JugglerTaskProperty):
    '''Class for the effort (estimate) of a juggler task'''

    #For converting the seconds (Jira) to days
    UNIT = 'd'
    FACTOR = 8.0 * 60 * 60

    DEFAULT_NAME = 'effort'
    MINIMAL_VALUE = 1.0 / 8
    DEFAULT_VALUE = MINIMAL_VALUE
    SUFFIX = UNIT

    def load_from_jira_issue(self, jira_issue):
        '''
        Load the object with data from a Jira issue

        Args:
            jira_issue (class): The Jira issue to load from
        '''
        self.set_value(self.DEFAULT_VALUE)
        if hasattr(jira_issue.fields, 'aggregatetimeoriginalestimate') and jira_issue.fields.aggregatetimeoriginalestimate:
            val = jira_issue.fields.aggregatetimeoriginalestimate
            self.set_value(val / self.FACTOR)
        else:
            logging.warning('No estimate found for %s, assuming %s%s', jira_issue.key, self.DEFAULT_VALUE, self.UNIT)

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

    def load_from_jira_issue(self, jira_issue):
        '''
        Load the object with data from a Jira issue

        Args:
            jira_issue (class): The Jira issue to load from
        '''
        self.set_value(self.DEFAULT_VALUE)
        if hasattr(jira_issue.fields, 'issuelinks'):
            for link in jira_issue.fields.issuelinks:
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

class JugglerTask(object):

    '''Class for a task for Task-Juggler'''

    DEFAULT_KEY = 'NOT_INITIALIZED'
    DEFAULT_SUMMARY = 'Task is not initialized'
    TEMPLATE = '''
task {id} "{key}: {description}" {{
{props}
}}
'''

    def __init__(self, jira_issue=None):
        logging.info('Create JugglerTask for %s', jira_issue.key)

        self.key = self.DEFAULT_KEY
        self.summary = self.DEFAULT_SUMMARY
        self.properties = {}

        if jira_issue:
            self.load_from_jira_issue(jira_issue)

    def load_from_jira_issue(self, jira_issue):
        '''
        Load the object with data from a Jira issue

        Args:
            jira_issue (class): The Jira issue to load from
        '''
        self.key = jira_issue.key
        self.summary = jira_issue.fields.summary.replace('\"', '\\\"')
        self.properties['allocate'] = JugglerTaskAllocate(jira_issue)
        self.properties['effort'] = JugglerTaskEffort(jira_issue)
        self.properties['depends'] = JugglerTaskDepends(jira_issue)

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

class JiraJuggler(object):

    '''Class for task-juggling Jira results'''

    def __init__(self, url, user, passwd, query):
        '''
        Construct a JIRA juggler object

        Args:
            url (str): URL to the JIRA server
            user (str): Username on JIRA server
            passwd (str): Password of username on JIRA server
            query (str): The Query to run on JIRA server
        '''

        logging.info('Jira server: %s', url)

        self.jirahandle = JIRA(url, basic_auth=(user, passwd))
        self.set_query(query)

    def set_query(self, query):
        '''
        Set the query for the JIRA juggler object

        Args:
            query (str): The Query to run on JIRA server
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

    def load_issues_from_jira(self):
        '''
        Load issues from Jira

        Returns:
            list: A list of dicts containing the Jira tickets
        '''
        tasks = []
        busy = True
        while busy:
            try:
                issues = self.jirahandle.search_issues(self.query, maxResults=JIRA_PAGE_SIZE, startAt=self.issue_count)
            except JIRAError:
                logging.error('Invalid Jira query "%s"', self.query)
                return None

            if len(issues) <= 0:
                busy = False

            self.issue_count += len(issues)

            for issue in issues:
                logging.debug('Retrieved %s: %s', issue.key, issue.fields.summary)
                tasks.append(JugglerTask(issue))

        self.validate_tasks(tasks)

        return tasks

    def juggle(self, output=None):
        '''
        Query JIRA and generate task-juggler output from given issues

        Args:
            output (str): Name of output file, for task-juggler
        '''
        issues = self.load_issues_from_jira()
        if not issues:
            return None
        if output:
            with open(output, 'w') as out:
                for issue in issues:
                    out.write(str(issue))
        return issues

if __name__ == "__main__":
    ARGPARSER = argparse.ArgumentParser()
    ARGPARSER.add_argument('-l', '--loglevel', dest='loglevel', default=DEFAULT_LOGLEVEL,
                           action='store', required=False,
                           help='Level for logging (strings from logging python package)')
    ARGPARSER.add_argument('-j', '--jira', dest='url', default=DEFAULT_JIRA_URL,
                           action='store', required=False,
                           help='URL to JIRA server')
    ARGPARSER.add_argument('-u', '--username', dest='username', default=DEFAULT_JIRA_USER,
                           action='store', required=True,
                           help='Your username on JIRA server')
    ARGPARSER.add_argument('-q', '--query', dest='query', default=DEFAULT_JIRA_QUERY,
                           action='store', required=True,
                           help='Query to perform on JIRA server')
    ARGPARSER.add_argument('-o', '--output', dest='output', default=DEFAULT_OUTPUT,
                           action='store', required=False,
                           help='Output .tjp file for task-juggler')
    ARGS = ARGPARSER.parse_args()

    set_logging_level(ARGS.loglevel)

    PASSWORD = getpass('Enter JIRA password for {user}: '.format(user=ARGS.username))

    JUGGLER = JiraJuggler(ARGS.url, ARGS.username, PASSWORD, ARGS.query)

    JUGGLER.juggle(ARGS.output)
