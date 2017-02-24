from tester_base import *
from model import *


class BodyTest(BaseTestCase):

    def test_insufficient_args(self):
        self.assertRaises(TypeError, Body)
        self.assertRaises(TypeError, Body, 'KOI-0012 b')
        self.assertRaises(TypeError, Body, 'KOI-0012 b', 'KOI-0012')

    def test_create(self):
        body_a = Body('planet A', set(), dict())
        body_b = Body('planet B', {'pB'}, {})
        self.assertTrue(body_a, Body('planet A', set(), dict()))
        self.assertNotEqual(body_a, body_b)


class PlanetTest(BaseTestCase):

    def test_eq(self):
        koi_0012 = Planet(
                'KOI-0012 b',
                'KOI-0012',
                {'KOI-0012 01'})
        self.assertEqual(
            koi_0012,
            Planet('KOI-0012 b', 'KOI-0012')
        )
        self.assertEqual(
            koi_0012,
            Planet('KOI-0012 01', 'KOI-0012'),
            "same planet with alternative name"
        )
        self.assertNotEqual(
            koi_0012,
            Planet('KOI-0012 02', 'KOI-0012'),
            "same system, different planet"
        )
        self.assertNotEqual(
            koi_0012,
            Planet('KOI-0012 b', 'KOI-0013'),
            "different system"
        )
        self.assertEqual(
            koi_0012,
            Planet('KOI-0012B', 'KOI-0012'),
            "spacing and capitalization should not matter"
        )


class SystemTest(BaseTestCase):

    def test_create(self):
        system_a = System('system A')
        planet_b = Planet('planet A', 'system B')
        system_b = System('system B', planets=[planet_b], all_names={'sysB'})

        self.assertEqual(system_a, System('system A'))
        self.assertNotEqual(system_a, system_b)


class PlanetUpdateTest(BaseTestCase):

    def test_create(self):
        update_a = PlanetUpdate("my update")
        update_b = PlanetUpdate("another update", True)

        self.assertEqual(repr(update_a),
                         "PlanetUpdate('my update', False, {})")
        self.assertNotEqual(repr(update_a), repr(update_b))


class PlanetarySysUpdateTest(BaseTestCase):

    def test_create(self):
        update_a = PlanetarySysUpdate("my update")
        update_b = PlanetarySysUpdate("another update", True)

        self.assertEqual(repr(update_a),
                         "PlanetarySysUpdate('my update', False, [])")
        self.assertNotEqual(repr(update_a), repr(update_b))
