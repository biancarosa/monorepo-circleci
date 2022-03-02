#!/usr/bin/env python3

import json
import os
import re
import subprocess

def checkout(revision):
    """
    Helper function for checking out a branch

    :param revision: The revision to checkout
    :type revision: str
    """
    subprocess.run(
        ['git', 'checkout', revision],
        check=True
    )

head = os.environ.get('CIRCLE_SHA1')
base_revision = os.environ.get('BASE_REVISION')
checkout(base_revision)  # Checkout base revision to make sure it is available for comparison
checkout(head)  # return to head commit

base = subprocess.run(
    ['git', 'merge-base', base_revision, head],
    check=True,
    capture_output=True
).stdout.decode('utf-8').strip()

if head == base:
    try:
    # If building on the same branch as BASE_REVISION, we will get the
    # current commit as merge base. In that case try to go back to the
    # first parent, i.e. the last state of this branch before the
    # merge, and use that as the base.
        base = subprocess.run(
            ['git', 'rev-parse', 'HEAD~1'], # FIXME this breaks on the first commit, fallback to something
            check=True,
            capture_output=True
        ).stdout.decode('utf-8').strip()
    except:
    # This can fail if this is the first commit of the repo, so that
    # HEAD~1 actually doesn't resolve. In this case we can compare
    # against this magic SHA below, which is the empty tree. The diff
    # to that is just the first commit as patch.
        base = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'

print('Comparing {}...{}'.format(base, head))
changes = subprocess.run(
    ['git', 'diff', '--name-only', base, head],
    check=True,
    capture_output=True
).stdout.decode('utf-8').splitlines()

print(changes)