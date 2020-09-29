"""unit tests for the mudscript module"""
import unittest
from swampymud.mudserver import MudServer
import swampymud.mudscript as ms
from swampymud.location import Location

class TestServerExport(unittest.TestCase):
    '''testing the server_export related functions'''

    def test_server_export(self):
        '''test that the server export function works'''
        with self.assertRaises(ms.SwampyException):
            ms.message_all("test!")
        with self.assertRaises(ms.SwampyException):
            ms.message_all("test!")
        # creating a test server with an uncommon port
        # if for some reason you cannot bind this port, feel free to change it
        test_server = MudServer(None, 17717)
        ms.export_server(test_server)
        # now we should be able to use the message_all function
        ms.message_all("hi there, friend!")
        ms.message_all("here's a second message!")
        # exporting 'None' should reset the server
        ms.export_server(None)
        with self.assertRaises(ms.SwampyException):
            ms.message_all("bye!!")

        # close the server
        test_server.shutdown()


    def test_server_export_type(self):
        '''test that server_export raises TypeError'''
        with self.assertRaises(TypeError):
            ms.export_server("My Server")
        with self.assertRaises(TypeError):
            ms.export_server(1)


class TestLocationExport(unittest.TestCase):
    '''testing the LocationExport class and import_location function'''

    def setUp(self):
        self.test_locations = {
            "Dungeon" : Location("Dungeon", "cold and scary!"),
            "Palace": Location("Dungeon", "gold and opulent!"),
            "Small Tavern": Location("Small Tavern", "a pleasant tavern")
        }

    def test_import_before_export(self):
        """test that import_location raises a SwampyException
        if no locations have been exported"""
        # importing location before any have been exported
        # should raise SwampyException
        with self.assertRaises(ms.SwampyException,
                               msg="Cannot access location "
                               "'Dungeon' (no locations are exported)"):
            ms.import_location("Dungeon")
        # briefly export locations, then return
        with ms.LocationExport(self.test_locations):
            pass
        # should raise SwampyException after calling __exit__
        with self.assertRaises(ms.SwampyException,
                               msg="Cannot access location "
                               "'Dungeon' (no locations are exported)"):
            ms.import_location("Dungeon")

    def test_bad_import_name(self):
        """test that calling import_location without a good name
        causes a KeyError"""
        with ms.LocationExport(self.test_locations):
            # trying to load a non-existent location 'Cavern'
            with self.assertRaises(KeyError,
                                   msg="Cannot access location "
                                   "'Cavern' (no locations with that name)"):
                ms.import_location("Cavern")
            # location names are case-sensitive
            with self.assertRaises(KeyError,
                                   msg="Cannot access location "
                                   "'dungeon' (no locations with that name)"):
                ms.import_location("dungeon")
            ms.import_location("Dungeon")
        # test with an empty location export
        # (also testing that previous locations were cleaned up)
        with ms.LocationExport({}):
            with self.assertRaises(KeyError,
                                   msg="Cannot access location "
                                   "'Dungeon' (no locations with that name)"):
                ms.import_location("Dungeon")

    def test_import_locations(self):
        """test that exported locations can be properly interacted with"""
        with ms.LocationExport(self.test_locations):
            dungeon = ms.import_location("Dungeon")
            self.assertTrue(dungeon is self.test_locations["Dungeon"])
            palace = ms.import_location("Palace")
            self.assertTrue(palace is self.test_locations["Palace"])
        # now try again
        with ms.LocationExport(self.test_locations):
            palace = ms.import_location("Small Tavern")
            self.assertTrue(palace is self.test_locations["Small Tavern"])
            dungeon = ms.import_location("Dungeon")
            self.assertTrue(dungeon is self.test_locations["Dungeon"])
