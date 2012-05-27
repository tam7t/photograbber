#!/usr/bin/env python
#
# Copyright (C) 2012 Ourbunny
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

# function repeater decorator
def repeat(func, n=10, standoff=1.5):
    """Execute a function repeatedly until success.

        @repeat
        def fail():
            print 'try fail...'
            throw new Exception()

        @repeat
        def pass():
            print 'pass'

        fail()
        pass()

    func: pointer to function
    n: retry the call <n> times before raising an error
    standoff: multiplier increment for each standoff
    """

    def wrapped(*args, **kwargs):
        retries = 0
        logger = logging.getLogger('repeat decorator')
        while True:
            try:
                return func(*args, **kwargs)
            except Exception, e:
                logger.error('failed function: %s' % e)
                if retries < n:
                    retries += 1
                    time.sleep(retries * standoff)
                else:
                    raise
    return wrapped

