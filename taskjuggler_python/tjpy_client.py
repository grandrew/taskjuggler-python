"""A sample CLI with API interaction."""

import logging

import click

from getpass import getpass
import argparse, sys
from . import utils
from jsonjuggler import *
import juggler

from airtable import Airtable

DEFAULT_LOGLEVEL = 'warning'
DEFAULT_OUTPUT = 'export.tjp'
log = logging.getLogger(__name__)


# @click.argument('')
# @click.command()
def main():
    logging.basicConfig(level=logging.INFO)

    ARGPARSER = argparse.ArgumentParser()
    ARGPARSER.add_argument('-l', '--loglevel', dest='loglevel', default=DEFAULT_LOGLEVEL,
                          action='store', required=False,
                          help='Level for logging (strings from logging python package: "warning", "info", "debug")')
    ARGPARSER.add_argument('-a', '--api', dest='api', default=None,
                          action='store', required=True, choices=['airtable'],
                          help='Execute specified API: only "airtable" is currently supported')
    ARGPARSER.add_argument('-k', '--api-key', dest='apikey', default="",
                          action='store', required=True,
                          help='Specify API key where appropriate (e.g. -k keyAnIuYcufa3dD)')
    ARGPARSER.add_argument('-b', '--base', dest='base', default="",
                          action='store', required=True,
                          help='Specify Base ID where appropriate (e.g. -b appA8ZuLosBV4GDSd)')
    ARGPARSER.add_argument('-t', '--table', dest='table', default="",
                          action='store', required=True,
                          help='Specify Table ID where appropriate (e.g. -t Tasks)')
    ARGPARSER.add_argument('-v', '--view', dest='view', default="",
                          action='store', required=True,
                          help='Specify Table View where appropriate (e.g. -v Work)')
    # ARGPARSER.add_argument('-o', '--output', dest='output', default=DEFAULT_OUTPUT,
    #                       action='store', required=False,
    #                       help='Output .tjp file for task-juggler')
    ARGS = ARGPARSER.parse_args()

    set_logging_level(ARGS.loglevel)

    # PASSWORD = getpass('Enter generic password for {user}: '.format(user=ARGS.username))
    
    airtable = Airtable(ARGS.base, ARGS.table, api_key=ARGS.apikey)
    
    JUGGLER = DictJuggler([x["fields"] for x in airtable.get_all(view=ARGS.view)])
    JUGGLER.run()
    
    for t in JUGGLER.walk(juggler.JugglerTask):
        airtable.update_by_field("id", t.get_id(), {"booking": t.walk(juggler.JugglerBooking)[0].decode()[0].isoformat()})
    
if __name__ == '__main__':  # pragma: no cover
    main()


#  {u'createdTime': u'2017-09-12T21:15:44.000Z',
#   u'fields': {u'APTDFF': u'inf',
#   u'ApHrsLeft': 99999,
#   u'Name': u'what to do in case of crash? new fund?',
#   u'Notes': u'invent a way to restart the fund',
#   u'Project': [u'recgvmfpkHpnT3PiO'],
#   u'Time track': 0,
#   u'effort': 0.5,
#   u'id': 67,
#   u'preference': 1000,
#   u'priority': u'Low'},
#   u'id': u'reczLPoGiWmgxN5nA'}]