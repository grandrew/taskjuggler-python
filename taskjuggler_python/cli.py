"""A sample CLI."""

import logging

import click

from getpass import getpass
import argparse
from . import utils
from juggler import *


DEFAULT_LOGLEVEL = 'warning'
DEFAULT_OUTPUT = 'export.tjp'
log = logging.getLogger(__name__)


@click.command()
@click.argument('feet')
def main(feet=None):
    logging.basicConfig(level=logging.INFO)

    meters = utils.feet_to_meters(feet)

    if meters is not None:
        click.echo(meters)
    
    return

    ARGPARSER = argparse.ArgumentParser()
    ARGPARSER.add_argument('-l', '--loglevel', dest='loglevel', default=DEFAULT_LOGLEVEL,
                          action='store', required=False,
                          help='Level for logging (strings from logging python package)')
    ARGPARSER.add_argument('-o', '--output', dest='output', default=DEFAULT_OUTPUT,
                          action='store', required=False,
                          help='Output .tjp file for task-juggler')
    ARGS = ARGPARSER.parse_args()

    set_logging_level(ARGS.loglevel)

    # PASSWORD = getpass('Enter generic password for {user}: '.format(user=ARGS.username))

    JUGGLER = GenericJuggler()

    JUGGLER.juggle()


if __name__ == '__main__':  # pragma: no cover
    main()
