# -*- coding: utf-8 -*-
{
    'name': 'Présence IMR',
    'version': '1.0.0',
    'category': 'hr',
    'sequence': 4,
    'author': 'Africa performances',
    'summary': 'management of employee presence',
    'description': """
Manage several employee
======================================

This App for account asset and update amort date at 31/12
    """,
    'depends': ["base", "hr", "hr_attendance", "hr_timesheet_sheet",],
    'data': [
        'presence.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,

    'qweb': ["static/src/xml/attendance.xml"],
}
