#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys

class Signal:
    """Signal with send/recieve"""

    def __init__(self, user, cli='signal-cli'):
        self.user = user
        self.cli = cli

    def run(self, *args):
        # this is a really nasty way to run it
        cmd = [self.cli, '-u', self.user] + list(map(str, args))
        return str(subprocess.check_output(cmd), encoding='UTF-8')

    def send(self, to, message, group=False):
        return self.run('send', to, '-m', message)

    def recv(self, timeout=0.5):
        output = self.run('receive', '--json', '-t', timeout)
        for line in output.split('\n'):
            if line != '':
                yield json.loads(line)

def main(args):
    '''Send a message and wait recieve any pending messages.'''
    # make sure you've registered your device before running:
    # ./bin/signal-cli -u +123456789 link -n signal-cli
    s = Signal(args['me'])
    s.send(args['to'], args['message'])
    for msg in s.recv():
        print(msg)

def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument('me', help='phone number you use for signal, ex: +1234567890')
    parser.add_argument('to', help='phone number of person on signal, ex: +1234567890')
    parser.add_argument('message', nargs='+', help='message body')

    args = vars(parser.parse_args(args))

    # message should be a string not a list
    args['message'] = ' '.join(args['message'])

    return args

if __name__ == '__main__':
    exit(main(parse_args(sys.argv[1:])))

