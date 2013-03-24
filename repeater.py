# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ourbunny
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import time

class DoNotRepeatError(Exception):
    """Raise DoNotRepeatError in a function to force repeat() to exit."""
    
    def __init__(self, error):
        Exception.__init__(self, error.message)
        self.error = error

def repeat(func, n=10, standoff=1.5):
    """Execute a function repeatedly until success (no exceptions raised).

    Args:
        func (function): The function to repeat

    Kwargs:
        n (int): The number of times to repeate `func` before raising an error
        standoff (float): Multiplier increment to wait between retrying `func`

    >>>import repeater.repeat

    >>>@repeater.repeat
    >>>def fail():
    >>>    print 'A'
    >>>    raise Exception()
    >>>    print 'B'

    >>>@repeater.repeat
    >>>    def pass():
    >>>    print 'B'

    >>>@repeater.repeat
    >>>def failpass():
    >>>    print 'C'
    >>>    raise repeater.DoNotRepeatError(Exception())
    >>>    print 'D'

    >>>fail() # prints 'A' 10 times, failing each time
    A
    A
    A
    A
    A
    A
    A
    A
    A
    A

    >>>pass() # prints 'B' once, succeeding on first try
    B

    >>>failpass() # prints 'C' once, then fails
    C

    """

    def wrapped(*args, **kwargs):
        retries = 0
        logger = logging.getLogger('repeater')
        while True:
            try:
                return func(*args, **kwargs)
            except DoNotRepeatError as e:
                # raise the exception that caused funciton failure
                raise e.error
            except Exception as e:
                logger.exception('Function failed: %s' % e)
                if retries < n:
                    retries += 1
                    time.sleep(retries * standoff)
                else:
                    raise
    return wrapped

