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

To begin using the Line Log, import the line log module:

::

  from r9050_line_log import Robot9050Sqlite3LineLog

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

Choosing the Hash Function
==========================

The Line Log offers a selection of hashing functions. For now, only
Python built-in hash functions from ``hashlib`` are supported.
BLAKE2b with 128-bit hashes is the default hash function.

Use the ``hash_fn_config`` argument to configure the hash function.
This argument expects configuration information in dicts.

Please note that the hash function may only be configured during the
creation of the log; the hash function **cannot be changed later**.

``hash_fn`` dict  Format
------------------------

There is only one mandatory option, ``hash_fn``, that selects the
hashing function by its name as a string.

::

   {'hash_fn': HASH_FUNCTION}

Call ``get_supported_hash_fns()`` for a list of acceptable choices for
``HASH_FUNCTION``.

Non-configurable hash functions
-------------------------------

Using MD5: ``{'hash_fn': 'md5'}``

Using SHA-1: ``{'hash_fn': 'sha1'}``

Using SHA-256: ``{'hash_fn': 'sha256'}``

Using SHA-512: ``{'hash_fn': 'sha512'}``

Example:

::

  sha256log = Robot9050Sqlite3LineLog(
    database='sha256log.sqlite3',
    action='create',
    hash_fn_config={'hash_fn': 'sha256'}
  )

The MD5 function is not recommended for general public use, due to its
weaknesses. `SHA-1's weaknesses`_ are currently not expected to be an
issue in the short message hashing use cases of this software.

.. _SHA-1's weaknesses: https://eprint.iacr.org/2020/014.pdf

Configurable hash functions
---------------------------

Some functions are configurable; but each hash function has its own
configurables. All configurables besides ``hash_fn`` are optional,
defaults will be used in place of missing options.

BLAKE2s

::

    {
        'hash_fn': 'blake2s',
        'digest_size': HASH_LENGTH,
        'key': KEY_BYTES,
        'salt': BYTES,
        'person': BYTES,
    }

``DIGEST_SIZE`` is an int from 1 to 32 inclusive. ``BYTES`` is a byte
array that may be up to 8 bytes long.

BLAKE2b

::

    {
        'hash_fn': 'blake2b',
        'digest_size': HASH_LENGTH,
        'key': KEY_BYTES,
        'salt': BYTES,
        'person': BYTES,
    }

``DIGEST_SIZE`` is an int from 1 to 64 inclusive.  ``BYTES`` is a byte
array that may be up to 16 bytes long.

`Scrypt`_

::

    {
        'salt': SALT_BYTES,
        'n': COST_FACTOR,
        'r': BLOCK_SIZE_FACTOR,
        'p': PARALLELIZATION,
        'dklen': HASH_LENGTH,
    }

``COST_FACTOR`` must be a power of two (``math.log2(COST_FACTOR)``
must be a whole number).

Examples:

::

  b2slog = Robot9050Sqlite3LineLog(
    database='blake2slog.sqlite3',
    action='create',
    hash_fn_config={
        'hash_fn': 'blake2s',
        'digest_size': 32
    }
  )

  # This is a very slow hash log for your edutainment

  scryptlog = Robot9050Sqlite3LineLog(
    database='scryptlog.sqlite3',
    action='create',
    hash_fn_config={
        'hash_fn': 'scrypt',
        'n': 8192,
        'r': 16,
        'p': 4096,
        'dklen': 128
    }

You may recognise that the keys and values in hash_fn_config directly mirror the arguments in the original hash functions.

.. _Scrypt: https://en.wikipedia.org/wiki/Scrypt

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

* BLAKE3 Support?

* Command-line tool?

* ``Robot9050RedisLineLog``: interface for Redis

* Unit Tests!

