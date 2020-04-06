import sqlite3
from sqlite3 import Error


class Database:
    """
    database handling through the oop way
    """

    def __init__(self, db):
        self.db_file = db
        self.connect = sqlite3.connect(self.db_file)
        self.cursor = self.connect.cursor()

    def insert_fingerprint(self, hash_item):
        '''
        insert fingerprints into the database
        :param hash_item: single iterables as returned by gen_hash function in basic ops
        :return:
        '''
        sha, (song, offset) = hash_item
        sha = str(sha)
        try:
            comm = '''INSERT INTO fingerprints(sha, song_id, offset) VALUES (?, ?, ?);'''
            entries = (sha, song, offset)
            self.cursor.execute(comm, entries)
            self.connect.commit()

        except Error as e:
            print('failed to push fingerprint into database')
            print(e)

    def query_signal(self, fingerprint):
        """
        match list structure [(song_name, offset), .....]
        :param fingerprint: contains only the sha1 fingerprint of the query song skipped by a step of 2. i.e sha_hash[::2]
        :return: match.
        """
        match = []

        try:
            comm = '''SELECT * FROM fingerprints WHERE sha = ?'''
            self.cursor.execute(comm, (fingerprint,))
            rows = self.cursor.fetchall()
            match = [(row[1], row[2]) for row in rows]

        except Error as e:
            print('No matching song found')
            print(e)

        return match

    def fetch_result(self, fingerprints):
        '''

        :param fingerprints: all the fingerprints from the query song. this method willl one by one match for
        all the sha1 hash in the fingerprints list which have a structure [sha1_hash, (song_id, offset)]. song id
        and offset in these fingerprints are of no use and just a by product of the reusable code
        :return:match list of structure [(song_id, offset_difference)... ]
        '''
        matches = []
        x = 0  # to count the number of collisions that we have
        for fp in fingerprints:
            x += 1
            sha_query, (song_id, offset) = fp
            match_for_this_sha = self.query_signal(sha_query)
            for mat in match_for_this_sha:
                # match contains song_id and difference in offset
                matches.append((mat[0], mat[1] - offset))
            if x % 10 == 0:
                print('HASH COLLISION COUNT: {}'.format(x))
            if x % 1000:
                break

        return matches
