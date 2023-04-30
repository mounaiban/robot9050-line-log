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

----
TODO
----

* Command-line tool?

* Document hash function configuration in more detail

* ``Robot9050RedisLineLog``: interface for Redis

* Unit Tests!

