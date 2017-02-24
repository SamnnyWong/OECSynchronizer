from tester_base import *
from astro_unit import *


class QuantityTest(BaseTestCase):
    def test_init_failed(self):
        invalid_numbers = [
            None,
            '',
            '   ',
        ]
        for num in invalid_numbers:
            with self.assertRaises(ValueError, msg=repr(num)):
                Quantity(num, None)

            q = Quantity('1', None, (num, num))
            self.assertIsNone(q.error, 'should remove during init')

    def test_init_negative_error(self):
        self.assertEqual(
            Quantity('1', error=('1', '1'), is_limit=False),
            Quantity('1', error=('-1', '1'), is_limit=False),
            "negative values are not allowed in error tuple"
        )

        self.assertEqual(
            Quantity('1', error=('1', '1'), is_limit=False),
            Quantity('1', error=('-1', '-1'), is_limit=False),
            "negative values are not allowed in error tuple"
        )

        q = Quantity('1', error=('-1', '2'), is_limit=True)
        self.assertEqual(('-1', '2'), q.error,
                         "negative values are allowed in limit tuple")

    def test_conversion_basic(self):
        km_m = [
            ('0', '0'),
            ('1.234', '1234'),
            ('1.2345', '1234.5'),
            ('1.2345e2', '1.2345e5'),
            ('1.2345e2', '123450'),
        ]

        for v_km, v_m in km_m:
            km = Quantity(v_km, 'km')
            m = Quantity(v_m, 'meter')
            self.assertEqual(m, km.to('meter'))
            self.assertEqual(km, m.to('km'))
            self.assertEqual(km, km.to('meter').to('km'))
            self.assertEqual(m, m.to('km').to('m'))

    def test_conversion_errors(self):
        self.assertEqual(
            Quantity('1.234', 'km', ('1e-3', '2e-3')),
            Quantity('1234', 'meter', ('1', '2')).to('km')
        )

    def test_conversion_numeric_error(self):
        self.assertEqual(
            Quantity('1.2', 'month'),
            Quantity('.1', 'year').to('month')
        )

    def test_conversion_custom_units(self):
        self.assertEqual(
            Quantity('5.97219e24', 'kg'),
            Quantity('1', 'M_e').to('kg')
        )
        self.assertEqual(
            Quantity('6.371e6', 'meter'),
            Quantity('1', 'R_e').to('meter')
        )

    def test_get_error_or_limit(self):
        self.assertEqual(
            ('1', '2'),
            Quantity('10', error=('9', '12'), is_limit=True)
            .get_error_or_limit(False)
        )

        self.assertEqual(
            ('9', '12'),
            Quantity('10', error=('1', '2'), is_limit=False)
            .get_error_or_limit(True)
        )

    def test_can_update_error(self):
        self.assertFalse(
            Quantity('1', error=None)
            .can_update_error(Quantity('2', error=None)),
            "case: none has error tuple"
        )

        self.assertFalse(
            Quantity('1', error=('1', '2'))
            .can_update_error(Quantity('2', error=None)),
            "case: new quantity has no error tuple, shouldn't erase existing"
        )

        self.assertTrue(
            Quantity('1', error=None)
            .can_update_error(Quantity('2', error=('1', '2'))),
            "case: old quantity has no error tuple, should update error values"
        )

        self.assertFalse(
            Quantity('1', error=('1', '2'), is_limit=False)
            .can_update_error(
                Quantity('1', error=('1.0', '2.0'), is_limit=False)
            )
        )

        self.assertTrue(
            Quantity('1', error=('1', '2'), is_limit=False)
            .can_update_error(
                Quantity('1', error=('1', '2'), is_limit=True)
            )
        )

        self.assertFalse(
            Quantity('1', error=('1', '2'), is_limit=False)
            .can_update_error(
                Quantity('1', error=('0', '3'), is_limit=True)
            )
        )