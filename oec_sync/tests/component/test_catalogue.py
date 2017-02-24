from tester_base import *
from catalogue import *
import io


SAMPLE = """
name: "Random Exoplanet Catalogue"
url: "http://catalogue.com/download-csv"
system_name: pl_hostname
planet_name: pl_name
field_map:
  semimajoraxis: #type="number"
    name: pl_orbsmax
    upperlimit: pl_orbsmaxerr1
    lowerlimit: pl_orbsmaxerr2
    unit: AU
  period:
    name: pl_orbper
    errorplus: pl_orbpererr1
    errorminus: pl_orbpererr2
    limit_flag: pl_obperlim
    unit: days
value_map:
  discoverymethodtype:
    imaging: Imaging
    microlensing: Microlensing
    RV: Radial Velocity
    timing: .*Timing.*
    transit: Transit
    number: pl_orbtper
"""


class CatalogueConfigTest(BaseTestCase):

    def test_init(self):
        c = CatalogueConfig(io.StringIO(SAMPLE))

        self.assertEqual("Random Exoplanet Catalogue", c.name)
        self.assertEqual("http://catalogue.com/download-csv", c.url)
        self.assertEqual("pl_hostname", c.system_name)
        self.assertEqual("pl_name", c.planet_name)

        self.assertEqual(2, len(c.field_map))

        self.assertDictEqual(
            {
                'name': 'pl_orbsmax',
                'upperlimit': 'pl_orbsmaxerr1',
                'lowerlimit': 'pl_orbsmaxerr2',
                'unit': 'AU'
            },
            c.field_map['semimajoraxis']
        )

        self.assertDictEqual(
            {
                'name': 'pl_orbper',
                'errorplus': 'pl_orbpererr1',
                'errorminus': 'pl_orbpererr2',
                'limit_flag': 'pl_obperlim',
                'unit': 'days'
            },
            c.field_map['period']
        )

    def test_nasa(self):
        configfile = SrcPath.abs('sync_config', 'NASA.yml')
        with open(configfile, 'r') as f:
            c = CatalogueConfig(f)
            self.assertEqual('NASA Exoplanet Archive', c.name)

    def test_exo_eu(self):
        configfile = SrcPath.abs('sync_config', 'exoplanet.yml')
        with open(configfile, 'r') as f:
            c = CatalogueConfig(f)
            self.assertEqual('Exoplanet.eu', c.name)
