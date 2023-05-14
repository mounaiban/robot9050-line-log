"""
ROBOT9050 Line Log WIP

"""
#
# Copyright (C) 2023 Moses Chong
#
# Licensed under the GNU General Public License Version 3
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#
# Please see README.rst for details.
# This module uses spaces, not tabs.
# Only for Python 3.6 or higher (requires f-strings and secrets).
# There are notes at the bottom of this module.
#

import hashlib
import sqlite3
from secrets import token_bytes

class Robot9050LineLog:
    """
    ROBOT9050 Line Log prototype/interface

    This class defines the ROBOT9050 Line Log API
    """
    def __init__(self, **kwargs):
        raise NotImplementedError('TODO: Create repository object')

    def create(self, hashfn_config):
        """Create or prepare database in file or on server"""
        raise NotImplementedError('TODO: Create/prepare database')

    def dbck(self):
        """Check if database is a valid, identified Line Log"""
        raise NotImplementedError('TODO: Verify database is ready to use')

    def get_hash_fn_config(self):
        raise NotImplementedError('TODO: Get hash function configuration')

    @classmethod
    def get_supported_hash_fns(self):
        raise NotImplementedError('TODO: Get supported hash functions')

    def lookup(self, line):
        """
        Check if a string "line" has been added to the log, return
        the number of times it has been logged as a positive integer.
        A value of zero means the string has not yet been logged.

        This method does not write anything into the log.
        """
        raise NotImplementedError('TODO: Check if line has been seen')

    def add(self, line):
        """
        Add a string "line" to the log if it has not yet been added,
        or bump its count otherwise.
        """
        raise NotImplementedError('TODO: Add line or bump count')

    def version(self, line):
        """Return line log database format version"""
        raise NotImplementedError('TODO: Return DB format version')

class Robot9050Sqlite3LineLog(Robot9050LineLog):
    """
    ROBOT9050 SQLite3 Repository

    Object for accessing ROBOT9050 logs stored in an SQLite3 DB
    """
    ENCODING = 'ascii'
    ENCODING_LINES = 'utf16'
    FORMAT_VER = '1'  # string, to allow suffixes
    HASHFN_KEY = 'hash_fn'
    HASHFN_DEFAULT = 'blake2b'
    LOG_ID = 'ID:ROBOT9050-line-log'
    TABLE_NAME = 'Robot9050LineLog'
    TABLE_COLS = ('k', 'v')
    TYPE_SEP = ':'
    TYPE_SEP_BYTES = b':'
    PREFIX_CONFIG = 'CFG'
    SUPPORTED_HASH_FNS = {
        # NOTE: BLAKE2 tree hashing features are not used
        'blake2b' : {
            'digest_size': 16,
            'key': token_bytes(32),
            'salt': token_bytes(16), # PROTIP: max 16B for b2b
            'person': token_bytes(16), # PROTIP: max 16B for b2b
            'usedforsecurity': True,
        },
        'blake2s' : {
            'digest_size': 16,
            'key': token_bytes(32),
            'salt': token_bytes(8), # PROTIP: max 8B for b2s
            'person': token_bytes(8), # PROTIP: max 8B for b2s
            'usedforsecurity': True,
        },
        'md5' : {}, # NOTE: MD5 has been broken; use for tests only
        'scrypt': {
            'salt': token_bytes(64),
            'n': 64,
            'r': 8,
            'p': 2048,
            'dklen': 64
        }, # very slow, use cases not yet known
        'sha1': {}, # NOTE: SHA-1 has been broken; use for tests only
        'sha256' : {},
        'sha512' : {},
    }
    # Default values corresponding to supported configurables
    # The value type is the same as that of the default value

    def __init__(self, **kwargs):
        """
        Create or open a database file.

        Supported kwargs:

        * action: 'create' or 'open'

        * hashfn_config: dict containing hash function options

        Examples:

        xlog = Robot9050Sqlite3LineLog(
            action='create',
            hashfn_config={'hash_fn': 'blake2b'},
            database='xlog.r9050_log'
        )

        xlog = Robot9050Sqlite3LineLog(
            action='open', database='xlog.r9050_log'
        )

        """
        # TODO: document passthru for sqlite3.connect args
        ka = kwargs.copy()
        self._hashfn = None
        self._hashargs = None # TODO: less misleading than _hashcfg?
        action = ka.pop('action', 'open')
        hashfn_config = ka.pop('hash_fn_config', None)
        self._connection = sqlite3.connect(**ka)
        self._cursor = self._connection.cursor()
        if action=='open':
            if not self.dbck():
                raise RuntimeError('database not found or not ready')
        elif action=='create':
            self.create(hashfn_config=hashfn_config)
        self._setup()

    ### Implementation Details

    def _put_config_item(self, cfgk, cfgv):
        # prepare k
        if type(cfgk) is not str: raise TypeError('config key cfgk must be str')
        k = bytes(
            f"{self.PREFIX_CONFIG}{self.TYPE_SEP}{cfgk}",
            encoding=self.ENCODING
        )
        # prepare v
        if type(cfgv) not in (bool, bytes, int, str):
            raise TypeError('value type must be bytes, bool, int or str')
        # write
        sc_del = f"DELETE FROM {self.TABLE_NAME} WHERE k = ?;"
        sc = f"INSERT INTO {self.TABLE_NAME} VALUES (?, ?);"
        self._cursor.execute(sc_del, (k,))
        self._cursor.execute(sc, (k, cfgv,))
        self._connection.commit()

    def _get_config_item(self, cfgk):
        sc = f"""
            SELECT {self.TABLE_COLS[1]} FROM {self.TABLE_NAME}
            WHERE {self.TABLE_COLS[0]} = CAST(? AS BLOB)
            ORDER BY {self.TABLE_COLS[0]} ASC
            LIMIT 1;
        """
        k = f"{self.PREFIX_CONFIG}{self.TYPE_SEP}{cfgk}"
        return next(self._cursor.execute(sc, (k,)))[0]

    def _setup(self):
        """Load and apply configuration information"""
        self._hashargs = self.get_hash_fn_config()
        hfn = self._hashargs.pop(self.HASHFN_KEY)
        self._hashfn = getattr(self, f'_get_hash_{hfn}')

    def _cols_and_id_ok(self):
        """
        Check if SQL table is present and correct, and
        identifier is present

        """
        sc = f"""
            SELECT COUNT(*) FROM {self.TABLE_NAME}
            WHERE {self.TABLE_COLS[0]} = CAST(? AS BLOB);
        """
        try:
            i = next(self._cursor.execute(sc, (self.LOG_ID,)))
            if i[0] >= 1: return True
        except:
            return False
        # TODO: more detailed result codes instead of True/False
        # TODO: warn if there is more than one ID

    def _cursor_ok(self):
        """
        Check if SQLite Cursor is configured and matches connection
        """
        if not self._cursor: return False
        return self._cursor.connection is self._connection

    ### Hash Generation Methods

    def _get_hash_blake2b(self, line):
        lbytes = bytes(line, encoding=self.ENCODING_LINES)
        return hashlib.blake2b(lbytes, **self._hashargs).digest()

    def _get_hash_blake2s(self, line):
        lbytes = bytes(line, encoding=self.ENCODING_LINES)
        return hashlib.blake2s(lbytes, **self._hashargs).digest()

    def _get_hash_md5(self, line):
        lbytes = bytes(line, encoding=self.ENCODING_LINES)
        return hashlib.md5(lbytes).digest()

    def _get_hash_scrypt(self, line):
        lbytes = bytes(line, encoding=self.ENCODING_LINES)
        return hashlib.scrypt(lbytes, **self._hashargs)
        # PROTIP: As of 3.11, Python scrypt support in hashlib
        # is not implemented as an object, but as a function

    def _get_hash_sha1(self, line):
        lbytes = bytes(line, encoding=self.ENCODING_LINES)
        return hashlib.sha1(lbytes).digest()

    def _get_hash_sha256(self, line):
        lbytes = bytes(line, encoding=self.ENCODING_LINES)
        return hashlib.sha256(lbytes).digest()

    def _get_hash_sha512(self, line):
        lbytes = bytes(line, encoding=self.ENCODING_LINES)
        return hashlib.sha512(lbytes).digest()

    ### User Methods

    def create(self, hashfn_config=None):
        if not self._cursor:
            raise sqlite3.DatabaseError('database connection broken: no cursor')
        elif not self._cursor_ok():
            raise sqlite3.DatabaseError('cursor-connection mismatch')
        elif self._cols_and_id_ok():
            raise ValueError('line log already exists at location')
        # DB is ok, move on to configuration
        elif not hashfn_config:
            hashfn_config = {self.HASHFN_KEY: self.HASHFN_DEFAULT}
        elif self.HASHFN_KEY not in hashfn_config:
            raise KeyError(f'please specify the {self.HASHFN_KEY} argument')
        elif hashfn_config[self.HASHFN_KEY] not in self.SUPPORTED_HASH_FNS:
            raise KeyError(
                f'hash function {hashfn_config[self.HASHFN_KEY]} not supported'
            )
        if self._cursor_ok():
            tspec = f"{self.TABLE_COLS[0]} BLOB, {self.TABLE_COLS[1]}"
            # had to hardcode, only keys are blobs.
            sc_create = f"CREATE TABLE IF NOT EXISTS {self.TABLE_NAME}({tspec})"
            sc_mark = f"INSERT INTO {self.TABLE_NAME} VALUES (?,?)"
            self._cursor.execute(sc_create)
            self._cursor.execute(
                sc_mark,
                (bytes(self.LOG_ID, encoding=self.ENCODING), self.FORMAT_VER,)
            )
            # write hash function config
            hfn: str
            if not hashfn_config:
                hashfn_config = self.SUPPORTED_HASH_FNS[self.HASHFN_DEFAULT]
                hfn = self.HASHFN_DEFAULT
            else:
                hfn = hashfn_config[self.HASHFN_KEY]
            defaults = self.SUPPORTED_HASH_FNS[hfn]
            self._put_config_item(self.HASHFN_KEY, hfn)
            kiter = (x for x in defaults if x != self.HASHFN_KEY)
            val = None
            for k in kiter:
                if k not in hashfn_config:
                    val = defaults[k]
                else:
                    val = hashfn_config[k]
                self._put_config_item(f"{hfn}_{k}", val)
            self._connection.commit()
            return True
        else:
            raise RuntimeError('unhandled condition')

    def dbck(self):
        if not self._cursor:
            raise sqlite3.DatabaseError('database connection broken: no cursor')
        elif not self._cursor_ok():
            raise sqlite3.DatabaseError('cursor-connection mismatch')
        else: return self._cols_and_id_ok()

    def get_hash_fn_config(self):
        cfg = {}
        hfn = self._get_config_item(self.HASHFN_KEY)
        if hfn not in self.SUPPORTED_HASH_FNS:
            raise ValueError(f"unsupported hash function: {hfn}")
        else:
            cfg[self.HASHFN_KEY] = hfn
            spec = self.SUPPORTED_HASH_FNS[hfn]
            for k in (x for x in spec if not x.startswith('_')):
                val = self._get_config_item(f"{hfn}_{k}")
                cfg[k] = type(spec[k])(val)
        return cfg

    @classmethod
    def get_supported_hash_fns(self):
        return tuple(self.SUPPORTED_HASH_FNS)

    def lookup(self, line):
        # TODO: script is identical to _get_config_item's, consolidate?
        sc = f"""
            SELECT {self.TABLE_COLS[1]} FROM {self.TABLE_NAME}
            WHERE {self.TABLE_COLS[0]} = CAST (? AS BLOB)
            ORDER BY {self.TABLE_COLS[0]} ASC
            LIMIT 1;
        """
        fhash = b''.join((self.TYPE_SEP_BYTES, self._hashfn(line),))
        r = self._cursor.execute(sc, (fhash,))
        try: return next(r)[0]
        except StopIteration: return 0

    def add(self, line):
        count = self.lookup(line)
        fhash = b''.join((self.TYPE_SEP_BYTES, self._hashfn(line),))
        if not count:
            sc_ins = f"INSERT INTO {self.TABLE_NAME} VALUES (?, ?);"
            self._cursor.execute(sc_ins, (fhash, 1))
        elif count >= 1:
            sc_bump = f"""
                UPDATE {self.TABLE_NAME}
                SET {self.TABLE_COLS[1]} = {self.TABLE_COLS[1]} + 1
                WHERE {self.TABLE_COLS[0]} = ?
            """
            self._cursor.execute(sc_bump, (fhash,))
        self._connection.commit()

    def version(self):
        sc = f"""
            SELECT {self.TABLE_COLS[1]} FROM {self.TABLE_NAME}
            WHERE {self.TABLE_COLS[0]} = CAST ('{self.LOG_ID}' AS BLOB)
            ORDER BY {self.TABLE_COLS[0]} ASC
            LIMIT 1;
        """
        r = self._cursor.execute(sc)
        return next(r)[0]

#
# Database Format
# ===============
#
# The format used herein attempts to be as compatible with key-value
# databases as possible. There are only keys and values. In table-
# based databases where are named columns, keys are stored in the 'k'
# column, values in the 'v' column.
#
# Keys have a name that comprise a type followed by the rest of the
# name separated by a colon (:, U+003A). Keys are blobs, or ASCII
# strings (which are basically human-readable blobs)
#
# File identification: an identifier is stored under a key with prefix
# 'ID:' followed by an id string.
# Example: 'ID:R9050-log-1.0'
#
# Configuration: values with prefix of 'CFG:' are config values.
# Example: 'CFG:HashAlgo' : 'blake2b'
#
# Hashes: stored in keys with an empty type. Accompanying values are
# unsigned int counts indicating the number of attempts to add a line
# hash.
#
# Currently, values can be int, blob or True/False.
#
# Python Example
# ==============
#
# db = {
#   b'CFG:HashType'                        : b'blake2b',
#   b'CFG:HashLength'                      : 64,
#   b':)APS\x98_\xee\x0cr\xf3Hg7y\xcb\x8d' : 69,
#   b":b' \xeao\x8fNe\xa16~+\xdeh7.\xb5\\' : 420
# }
#
