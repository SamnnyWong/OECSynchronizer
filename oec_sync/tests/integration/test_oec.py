from tester_base import *
from shutil import copyfile
from oec import *
from astro_unit import Quantity


class AdapterTest(BaseTestCase):
    def test_read_system(self):
        adapter = Adapter()
        system = adapter.read_system(os.path.join(self.TESTS_ROOT,
                                                  'test_sample',
                                                  'KOI-0012.xml'))
        self.assertEqual('KOI-0012', system.name)
        self.assertEqual(1, len(system.planets))

        planet = system.planets[0]
        self.assertEqual('KOI-0012 b', planet.name)
        self.assertSetEqual(
            {'KOI-0012 b', 'KOI-0012 01'},
            planet.all_names
        )

        self.assertEqual(
            Quantity('1.22115', 'R_j', ('0.60146', '0.60146')),
            planet.prop['radius']
        )

        self.assertEqual(
            Quantity(
                '17.855149000000',
                'days',
                ('1.0000000e-05', '1.0000000e-05')),
            planet.prop['period']
        )

        self.assertEqual(
            Quantity(
                '2454979.5969200',
                'BJD',
                ('0.0002100', '0.0002100')
            ),
            planet.prop['transittime']
        )

    def test_read_system_alternate_names(self):
        adapter = Adapter()
        system = adapter.read_system(os.path.join(self.TESTS_ROOT,
                                                  'test_sample',
                                                  '2M 0746+20.xml'))

        self.assertEqual(2, len(system.all_names))
        self.assertIn('2M 0746+20', system.all_names)
        self.assertIn('2MASS J07464256+2000321', system.all_names)

    def test_update_single_planet(self):
        source_file = os.path.join(self.TESTS_ROOT,
                                   'test_sample', '1RXS1609.xml')
        test_file = os.path.join(self.data_path, os.path.basename(source_file))

        # copy a sample file to temporary path for testing
        copyfile(source_file, test_file)

        adapter = Adapter()

        # verify the original system file
        original_sys = adapter.read_system(test_file)
        self.assertEqual('1.7',
                         original_sys.planets[0].prop['radius'].value,
                         "Unexpected original value")

        # construct an update
        update = PlanetarySysUpdate(
            '1RXS1609',
            planets=[
                PlanetUpdate(
                    '1RXS1609 b',
                    fields={
                        'radius': Quantity('42', 'R_j')
                    }
                )
            ]
        )

        succeeded = adapter.update_file(test_file, update)
        self.assertTrue(succeeded, "Update should be successful")
        modified_planet = adapter.read_system(test_file).planets[0]
        self.assertEqual('42',
                         modified_planet.prop['radius'].value,
                         "Unexpected final value")
        self.assertIsNone(modified_planet.prop['radius'].error)

        ##########
        # Test the error terms
        update.planets[0].fields['radius'].value = '42.42'
        update.planets[0].fields['radius'].error = ('1.23', '2.34')
        succeeded = adapter.update_file(test_file, update)
        self.assertTrue(succeeded, "Update should be successful")
        modified_planet = adapter.read_system(test_file).planets[0]
        self.assertEqual('42.42',
                         modified_planet.prop['radius'].value)
        self.assertFalse(modified_planet.prop['radius'].is_limit)
        self.assertEqual(('1.23', '2.34'),
                         modified_planet.prop['radius'].error)

        ##########
        # Test the limit terms
        update.planets[0].fields['radius'].value = '42'
        update.planets[0].fields['radius'].error = ('-41', '83')
        update.planets[0].fields['radius'].is_limit = True

        succeeded = adapter.update_file(test_file, update)
        self.assertTrue(succeeded, "Update should be successful")

        modified_planet = adapter.read_system(test_file).planets[0]
        self.assertEqual('42', modified_planet.prop['radius'].value)
        self.assertTrue(modified_planet.prop['radius'].is_limit)
        self.assertEqual(('-41', '83'), modified_planet.prop['radius'].error)

        ##########
        # Test writing of some new fields
        self.assertNotIn('age', original_sys.planets[0].prop)
        self.assertNotIn('period', original_sys.planets[0].prop)
        update.planets[0].fields.clear()
        update.planets[0].fields['age'] = Quantity('42',
                                                   unit='Gyr',
                                                   error=('1', '2'),
                                                   is_limit=False)
        update.planets[0].fields['period'] = Quantity('43',
                                                      unit='days',
                                                      error=('40', '45'),
                                                      is_limit=True)
        succeeded = adapter.update_file(test_file, update)
        self.assertTrue(succeeded)

        modified_planet = adapter.read_system(test_file).planets[0]
        self.assertEqual('42', modified_planet.prop['age'].value)
        self.assertEqual(('1', '2'), modified_planet.prop['age'].error)
        self.assertFalse(modified_planet.prop['age'].is_limit)

        self.assertEqual('43', modified_planet.prop['period'].value)
        self.assertEqual(('40', '45'), modified_planet.prop['period'].error)
        self.assertTrue(modified_planet.prop['period'].is_limit)

    def test_update_multi_planets(self):
        source_file = os.path.join(self.TESTS_ROOT,
                                   'test_sample', '14 Her.xml')
        test_file = os.path.join(self.data_path, os.path.basename(source_file))

        # copy a sample file to temporary path for testing
        copyfile(source_file, test_file)

        adapter = Adapter()

        # verify the original system file
        original_sys = adapter.read_system(test_file)
        self.assertEqual(2, len(original_sys.planets),
                         "There should be 2 planets in the system")

        self.assertEqual('4.975', original_sys.planets[0].prop['mass'].value)
        self.assertEqual('7.679', original_sys.planets[1].prop['mass'].value)

        # construct an update
        update = PlanetarySysUpdate(
                '14 Her',
                planets=[
                    PlanetUpdate(
                            '14 Her b',
                            fields={
                                'mass': Quantity('42.975',
                                                 unit='M_j',
                                                 error=('1', '2'),
                                                 is_limit=False)
                            }
                    ),
                    PlanetUpdate(
                            '14 Her c',
                            fields={
                                'mass': Quantity('42.679',
                                                 unit='M_j',
                                                 error=('40', '49'),
                                                 is_limit=True)
                            }
                    )
                ]
        )

        succeeded = adapter.update_file(test_file, update)
        self.assertTrue(succeeded)

        modified_sys = adapter.read_system(test_file)

        planet_b_mass = modified_sys.planets[0].prop['mass']
        self.assertEqual('42.975', planet_b_mass.value)
        self.assertEqual(('1', '2'), planet_b_mass.error)
        self.assertFalse(planet_b_mass.is_limit)

        planet_c_mass = modified_sys.planets[1].prop['mass']
        self.assertEqual('42.679', planet_c_mass.value)
        self.assertEqual(('40', '49'), planet_c_mass.error)
        self.assertTrue(planet_c_mass.is_limit)
