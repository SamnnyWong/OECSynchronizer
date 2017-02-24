from tester_base import *
from update_request import *
from syncutil import Helper, SrcPath


class UpdateRequestTest(BaseTestCase):
    SAMPLE_UPDATE = PlanetarySysUpdate(
        'BD+20 274', False,
        [
            PlanetUpdate('Some Planet A', False,
                         {'mass': Quantity('4.2', 'msini', ('0.1', '0.1'))}
                         )
        ]
    )

    def test_init(self):
        req = UpdateRequest(self.SAMPLE_UPDATE)
        self.assertEqual(self.SAMPLE_UPDATE, req.updates)
        self.assertIn('bd-20-274', req.branch,
                      "branch name should contain system name")
        self.assertEqual('Update BD+20 274', req.title)

        req = UpdateRequest(self.SAMPLE_UPDATE,
                            'My Title',
                            'My Message',
                            'Reference')
        self.assertEqual('My Title', req.title)
        self.assertEqual('My Message', req.message)
        self.assertEqual('Reference', req.reference)

    def test_get_summary(self):
        sysupd = RandomData.system_update()
        sysupd.name = 'KOI-0012'
        req = UpdateRequest(sysupd)

        self.assertRaises(FormatError, req.get_summary)

        req.reference = 'NASA Exoplanet Archive'
        self.assertEqual("Update KOI-0012\n"
                         "\n"
                         "Reference: NASA Exoplanet Archive",
                         req.get_summary())

        req.title = 'MyTitle'

        req.message = "I know what I am doing. Trust me."
        self.assertEqual("MyTitle\n"
                         "\n"
                         "I know what I am doing. Trust me.\n"
                         "Reference: NASA Exoplanet Archive",
                         req.get_summary())

    def test_from_pull_request(self):
        g = Github()

        oec = g.get_repo('teammask/open_exoplanet_catalogue')

        pull = oec.get_pull(1)  # pull request #1 is made for testing
        req = UpdateRequest.from_pull_request(pull)
        self.assertEqual('Just making a random pull request.', req.message)
        self.assertEqual('42', req.reference)

        # Checking if update is reconstructed correctly
        sys_upd = req.updates
        self.assertEqual('Kepler-44', sys_upd.name)
        self.assertEqual(1, len(sys_upd.planets))
        self.assertFalse(sys_upd.new)

        planet_upd = sys_upd.planets[0]
        self.assertEqual('Kepler-44 b', planet_upd.name)
        self.assertEqual(5, len(planet_upd.fields))
        self.assertFalse(planet_upd.new)

        self.assertEqual(
                Quantity('84.9642', 'deg', ('0.62', '0.50'), False),
                planet_upd.fields['inclination']
        )
        self.assertEqual(
                Quantity('3.246729342', 'days', ('0.0000030', '0.0000030'),
                         False),
                planet_upd.fields['period']
        )
        self.assertEqual(
                Quantity('1.0942', 'R_j', ('0.07', '0.07'), False),
                planet_upd.fields['radius']
        )
        self.assertEqual(
                Quantity('0.044642', 'AU', ('0.0011', '0.0011'), False),
                planet_upd.fields['semimajoraxis']
        )
        self.assertEqual(
                Quantity('2455187.1564042', 'BJD', ('0.00021', '0.00021'),
                         False),
                planet_upd.fields['transittime']
        )


class UpdateRequestDBTest(BaseTestCase):
    """
    This test class is based on the repository:
    https://github.com/teammask/DBTest
    """
    DB_REPO_NAME = "teammask/DBTest"

    def test_cache_invalidation(self):
        # typical initialization
        config = Helper.read_conf(SrcPath.abs("config.yml"))
        db_name = os.path.join(self.data_path, "requests.db")
        db = UpdateRequestDB(db_name,
                             config['gh_api_token'],
                             self.DB_REPO_NAME)
        db.fetch_all(force_full_sync=True)
        self.assertGreater(len(db.requests), 7)

        # initialize with different repository
        with shelve.open(db_name) as cache:
            cache['repo'] = 'SOMETHING ELSE'
        db = UpdateRequestDB(db_name,
                             config['gh_api_token'],
                             self.DB_REPO_NAME)
        self.assertLess(len(db.requests), 7)

        db.fetch_all(force_full_sync=True)
        self.assertGreater(len(db.requests), 7)

        # initialize with corrupted data
        with shelve.open(db_name) as cache:
            cache['1'] = None
            cache['2'] = 'a string'
            cache['3'] = 123
            cache['4'] = ['42', None]
            cache['5'] = 3.14
            cache['6'] = {1, 2, 34}
        db = UpdateRequestDB(db_name,
                             config['gh_api_token'],
                             self.DB_REPO_NAME)
        self.assertLess(len(db.requests), 7)

    def test_fetch(self):
        def verify_db(
                db_requests: Dict[str, Union[CachedRequest, IgnoredRequest]]):
            """Verifies the request db has the correct data."""
            # 1 is valid and open
            request_1 = db_requests['1'].request
            self.assertEqual("Update HAT-P-55", request_1.title)
            self.assertEqual("HAT-P-55", request_1.updates.name)
            self.assertEqual(1, len(request_1.updates.planets))
            self.assertEqual(3, len(request_1.updates.planets[0].fields))
            self.assertEqual(1, request_1.pullreq_num)
            self.assertFalse(request_1.rejected)

            # 8 is invalid
            self.assertEqual(IgnoredRequest.invalid, db_requests['8'])

            # 4 has been merged
            self.assertEqual(IgnoredRequest.merged, db_requests['4'])

            # 7 is valid and closed
            request_7 = db_requests['7'].request
            self.assertEqual("HD 66428", request_7.updates.name)
            self.assertTrue(request_7.rejected)

        config = Helper.read_conf(SrcPath.abs("config.yml"))
        db_name = os.path.join(self.data_path, "requests.db")

        # initialize the db and fetch the latest requests
        db = UpdateRequestDB(db_name,
                             config['gh_api_token'],
                             self.DB_REPO_NAME)
        db.fetch_all(force_full_sync=True)

        request_ids = set(db.requests.keys())
        self.assertGreater(len(request_ids), 1)
        verify_db(db.requests)

        # re-initialize the db without fetching
        db = UpdateRequestDB(db_name,
                             config['gh_api_token'],
                             self.DB_REPO_NAME)
        verify_db(db.requests)

    def test_get_similar(self):
        config = Helper.read_conf(SrcPath.abs("config.yml"))
        db_name = os.path.join(self.SHARED_PATH, "dbtest_requests.db")

        # initialize the db and fetch the latest requests
        db = UpdateRequestDB(db_name,
                             config['gh_api_token'],
                             self.DB_REPO_NAME)
        db.fetch_all(force_full_sync=False)

        # create a request that's the same as PR 1
        duplicate_request = UpdateRequest(
            PlanetarySysUpdate(
                    "HAT-P-55",
                    planets=[
                        PlanetUpdate("HAT-P-55 b",
                                     fields={
                                         "eccentricity": Quantity("0.139000"),
                                         "impactparameter": Quantity(
                                             "0.3920",
                                             error=("0.0860", "0.0730")),
                                         "period": Quantity(
                                             "3.58524670",
                                             unit='days',
                                             error=("0.00000640", "0.00000640")
                                         )
                                     })
                    ]),
            title="Test request",
            message="message",
            reference="UpdateRequestDBTest"
        )

        similar = db.get_similar(duplicate_request)
        self.assertIsNotNone(similar)
        self.assertEqual(1, similar.request.pullreq_num)

        # try submitting the request,
        # although it will always fail because we haven't pushed the branch
        # the db should still figure out it's a duplicate
        with self.assertRaises(DuplicateError):
            db.submit(duplicate_request)

        duplicate_request.updates.name = "HAT-P-42"
        similar = db.get_similar(duplicate_request)
        self.assertIsNone(similar)
