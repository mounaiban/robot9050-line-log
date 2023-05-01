===================
ROBOT9050: Line Log
===================

----------
Background
----------

This module is part of an attempt to design a log format and API for
ROBOT9050 an upcoming enforced originality system for social media
networks, chatrooms and forums.

ROBOT9050 is intended to be a modernisation of Dan Boger's `2009 Perl
implementation`_ of Randall Munroe's `ROBOT9000 concept`_; it
introduces a key-value-database-friendly storage format and
cryptographic hashes to take on messages of arbitrary length.

This proof of concept is implemented in Python with the goal of using
as little third-party dependencies as possible.

All material in this repository is licensed under the `terms and
conditions`_ of the GNU General Public License, version 3 or later.

.. _2009 Perl implementation: https://github.com/zigdon/ROBOT9000

.. _ROBOT9000 concept: https://blog.xkcd.com/2008/01/14/robot9000-and-xkcd-signal-attacking-noise-in-chat/

.. _terms and conditions: https://www.gnu.org/licenses/gpl-3.0.html

-----
HOWTO
-----

Basics
======

First, create a line log database. Use the ``action`` argument with a
string value ``'create'``. This example creates an in-memory SQLite 3
Line Log, with a BLAKE2B hashing function:

::

  elog = Robot9050Sqlite3LineLog(database=':memory:', action='create')

To create a persistent log in the file system, just use a filesystem
path instead for ``database``:

::

  elog = Robot9050Sqlite3LineLog(database='elog.sqlite3', action='create')

To open a file ``elog.sqlite3`` call:

::

  elog = RobotSqlite3LineLog(database='elog.sqlite3')

The default action is ``open``, so there is no need to specify this in
the arguments.

To record lines, simply use the ``add`` method:

::

   elog.add('lol')

Check the number of times a line has been recorded with ``lookup``:

::

   >>> elog.lookup('lol')
   1

   >>> elog.add('lol')
   >>> elog.add('lol')
   >>> elog.lookup('lol')
   3

Limitations
===========

The Line Log does not attempt to identify visually-similar but
digitally distinct messages such as suffixes, additional spaces and
similar-looking glyphs:

::

   >>> elog.add('lol')
   >>> elog.lookup('lol 4529345')
   0

   >>> elog.lookup('𝓁𝒐𝓁')
   0

   >>> elog.lookup('lol ')
   0

If used as a part of an originality-enforcement system, additional
pre-processing measures may be required to ensure the effectiveness
of the system.

----
TODO
----

* Command-line tool?

* Document hash function configuration in more detail

* ``Robot9050RedisLineLog``: interface for Redis

* Unit Tests!

