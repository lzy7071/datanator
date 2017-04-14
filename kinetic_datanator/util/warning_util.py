""" Warning utilities

:Author: Yosef Roth <yosefdroth@gmail.com>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-04-13
:Copyright: 2017, Karr Lab
:License: MIT
"""

from requests.packages import urllib3
import openbabel


def disable_warnings():
    """ Disable warning messages from openbabel and urllib """
    openbabel.obErrorLog.SetOutputLevel(openbabel.obError)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def enable_warnings():
    """ Enable warning messages from openbabel and urllib """
    openbabel.obErrorLog.SetOutputLevel(openbabel.obWarning)
    urllib3.warnings.resetwarnings()
