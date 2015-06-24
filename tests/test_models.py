from daapserver.models import Server, Database, Item

import unittest


class ModelsTest(unittest.TestCase):
    """
    Test models.
    """

    def test_store(self):
        """
        Test store references stay the same.
        """

        server = Server()

        database = Database(id=1, name="Database A")
        server.databases.add(database)

        item = Item(id=2, name="Item A")
        database.items.add(item)

        self.assertEqual(
            server.databases.store,
            server.databases(revision=1).store)
        self.assertEqual(
            server.databases[1].items.store,
            server.databases[1].items(revision=1).store)
        self.assertEqual(
            server.databases(revision=1)[1].items.store,
            server.databases[1].items(revision=1).store)

    def test_basis(self):
        """
        Test basic functionality.
        """

        server = Server()
        database = Database(id=1, name="Database A")
        server.databases.add(database)

        self.assertListEqual(server.databases.keys(), [1])

        database = Database(id=2, name="Database B")
        server.databases.add(database)

        self.assertListEqual(server.databases.keys(), [2, 1])

        server.commit()
        server.databases.remove(database)
        server.commit()

        self.assertListEqual(server.databases.keys(), [1])
        self.assertListEqual(server.databases(revision=2).keys(), [1])
        self.assertListEqual(server.databases(revision=1).keys(), [2, 1])

        with self.assertRaises(KeyError):
            server.databases[2]

        database = Database(id=3, name="Database C")

        server.databases.add(database)
        server.commit()

        self.assertListEqual(server.databases.keys(), [3, 1])
        self.assertListEqual(server.databases(revision=3).keys(), [3, 1])
        self.assertListEqual(server.databases(revision=2).keys(), [1])
        self.assertListEqual(server.databases(revision=1).keys(), [2, 1])

    def test_nested(self):
        """
        Test nesting of objects, with different revisions.
        """

        server = Server()

        server.commit()
        server.commit()
        server.commit()
        server.commit()
        server.commit()

        database = Database(id=1, name="Database A")

        server.databases.add(database)
        server.databases.remove(database)

        database = Database(id=2, name="Database B")

        item = Item(id=3, name="Item A")
        database.items.add(item)

        server.databases.add(database)
        database.items.add(item)

        self.assertEqual(server.revision, 5)

        self.assertListEqual(server.databases.keys(), [2])
        self.assertListEqual(server.databases(revision=6).keys(), [2])
        self.assertListEqual(server.databases(revision=5).keys(), [])
        self.assertListEqual(server.databases(revision=4).keys(), [])
        self.assertListEqual(server.databases(revision=3).keys(), [])
        self.assertListEqual(server.databases(revision=2).keys(), [])
        self.assertListEqual(server.databases(revision=1).keys(), [])

        with self.assertRaises(KeyError):
            server.databases[1]

        self.assertListEqual(server.databases[2].items.keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=1).keys(), [3])

        with self.assertRaises(ValueError):
            # Item was added to a database that was not in a server before
            # adding.
            self.assertListEqual(
                server.databases[2].items(revision=2).keys(), [3])

        server.commit()

        self.assertListEqual(server.databases[2].items.keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=7).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=6).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=5).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=4).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=3).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=2).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=1).keys(), [3])

    def test_diff(self):
        """
        Test diff of two sets, for updated and removed items.
        """

        server = Server()

        database = Database(id=1, name="Database A")
        server.databases.add(database)

        item = Item(id=2, name="Item A")
        database.items.add(item)

        server.commit()

        item = Item(id=2, name="Item A, version 2")
        database.items.add(item)

        self.assertEqual(server.revision, 1)

        items_1 = database.items(revision=1)
        items_2 = database.items(revision=2)

        self.assertListEqual(items_2.keys(), [2])
        self.assertListEqual(list(items_2.updated(items_1)), [2])

        server.commit()

        database.items.remove(item)

        server.commit()

        items_1 = database.items(revision=1)
        items_2 = database.items(revision=2)
        items_3 = database.items(revision=3)

        self.assertListEqual(items_1.keys(), [2])
        self.assertListEqual(items_2.keys(), [2])
        self.assertListEqual(items_3.keys(), [])
        self.assertListEqual(list(items_3.removed(items_1)), [2])
        self.assertListEqual(list(items_3.removed(items_2)), [2])
        self.assertListEqual(list(items_3.removed(items_3)), [])
