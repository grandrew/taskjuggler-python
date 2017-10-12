"""A sample CLI with API interaction."""

import logging

from getpass import getpass
import argparse, sys, datetime
from jsonjuggler import *
import juggler

import dateutil.parser

from airtable import Airtable

DEFAULT_LOGLEVEL = 'warning'
# DEFAULT_OUTPUT = 'export.tjp'
log = logging.getLogger(__name__)

def main():
    logging.basicConfig(level=logging.WARN)

    ARGPARSER = argparse.ArgumentParser()
    ARGPARSER.add_argument('-l', '--loglevel', dest='loglevel', default=DEFAULT_LOGLEVEL,
                          action='store', required=False, choices=["debug", "info", "warn", "error"],
                          help='Level for logging (strings from logging python package: "warn", "info", "debug")')
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
    ARGPARSER.add_argument('--dry-run', dest='dryrun', default=False,
                          action='store_true', required=False,
                          help='Do not commit calculation results')
    # ARGPARSER.add_argument('-o', '--output', dest='output', default=DEFAULT_OUTPUT,
    #                       action='store', required=False,
    #                       help='Output .tjp file for task-juggler')
    ARGS = ARGPARSER.parse_args()

    set_logging_level(ARGS.loglevel)

    # PASSWORD = getpass('Enter generic password for {user}: '.format(user=ARGS.username))
    
    airtable = Airtable(ARGS.base, ARGS.table, api_key=ARGS.apikey)
    
    data = [x["fields"] for x in airtable.get_all(view=ARGS.view)] 
    for rec in data:
        preference = 0
        if "preference" in rec:
            preference = int(rec['preference'])
        if "priority" in rec:
            if rec["priority"].lower() == "low":
                pri = preference + 100
            elif rec["priority"].lower() == "high":
                pri = preference + 200
            elif rec["priority"].lower() == "critical":
                pri = preference + 300
            else:
                pri = 1
        else:
            pri = preference + 100 # low
        rec["priority"] = pri
        if 'appointment' in rec:
            rec['start'] = rec['appointment']
            del rec["priority"] # tasks scheduling is not guaranteed if priority is set
        if 'depends' in rec:
            rec['depends'] = [int(x) for x in re.findall(r"[\w']+", rec["depends"])]
        if "priority" in rec and  "deadline" in rec and not rec["priority"] >= 300:
            diff_days = (datetime.datetime.now() - dateutil.parser.parse(rec["deadline"])).days
            if diff_days < 0: diff_days = 0
            rec["priority"] = rec["priority"] + diff_days * 3
            if rec["priority"] >= 250: rec["priority"] = 250
    
    JUGGLER = DictJuggler(data)
    JUGGLER.run()
    
    if ARGS.dryrun: return
    
    for t in JUGGLER.walk(juggler.JugglerTask):
        airtable.update_by_field("id", t.get_id(), {"booking": t.walk(juggler.JugglerBooking)[0].decode()[0].isoformat()})
    
if __name__ == '__main__':  # pragma: no cover
    main()
