from tester_base import *
from comparer import *


class DataCompareTest(BaseTestCase):

    PL_KOI_0012B = Planet(
        'KOI-0012 b',
        'KOI-0012',
        all_names={
            'KOI-0012 01'
        },
        prop={
            'radius': Quantity(
                '1.22115',
                'R_j',
                error=('0.60146', '0.60146'),
            ),
            'period': Quantity(
                '17.855149000000',
                'BJD',
                error=('1.0000000e-05', '1.0000000e-05'),
            ),
            'transittime': Quantity(
                '2454979.5969200',
                'BJD',
                error=('0.0002100', '0.0002100')
            )
        }
    )

    def test_basic(self):
        s1 = System(
            'KOI-0012',
            planets=[
                self.PL_KOI_0012B
            ]
        )
        s2 = System(
            'KOI-0012',
            planets=[
                Planet(
                    'KOI-0012 b',
                    'KOI-0012',
                    prop={
                        'radius': Quantity(
                            '1.22115',
                            'R_j',
                            error=('0.60146', '0.60146'),
                        )
                    }
                )
            ]
        )
        sysupd = data_compare(s1, s2)
        self.assertIsNone(sysupd)

        # test alternate name
        s2.planets[0].name = 'KOI-0012 01'
        sysupd = data_compare(s1, s2)
        self.assertIsNone(sysupd)

        # make some changes
        s2.planets[0].prop['radius'].value = '1.2211542'
        sysupd = data_compare(s1, s2)
        self.assertIsNotNone(sysupd)
        self.assertEqual('KOI-0012', sysupd.name)
        self.assertEqual(1, len(sysupd.planets))

        plupd = sysupd.planets[0]
        self.assertEqual('KOI-0012 b', plupd.name)
        self.assertFalse(plupd.new)
        self.assertEqual(1, len(plupd.fields))
        self.assertEqual('1.2211542', plupd.fields['radius'].value)
