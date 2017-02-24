import unittest
import os
import sys
import shutil
import random
import string
import logging.config
from datetime import datetime
from model import *
from syncutil import SrcPath
import stat

LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s]'
                      '[%(module)15s.%(funcName)-15s:%(lineno)-4s]'
                      '[%(levelname)-5s] %(message)s'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
}
logging.config.dictConfig(LOG_CONFIG)


class BaseTestCase(unittest.TestCase):
    # root folder containing tests
    TESTS_ROOT = SrcPath.abs('tests')

    # this folder will be ignored by git
    TEST_DATA = os.path.join(TESTS_ROOT, '.cache')

    # this folder contains private folders for each test run
    INDIVIDUAL_PATH = os.path.join(TEST_DATA, 'individual')

    # this folder contains everything that's shared among tests
    SHARED_PATH = os.path.join(TEST_DATA, 'shared')

    # private folders created for the last test run
    data_paths = []

    # outcome of the last test run
    result = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_path = None

    @classmethod
    def setUpClass(cls):
        """
        Injects our `setUp` or `tearDown` method to the inherited test case.
        """
        if cls is not BaseTestCase:
            if cls.setUp is not BaseTestCase.setUp:
                orig_setup = cls.setUp

                def setup_override(self):
                    """Overridden setup method"""
                    BaseTestCase.setUp(self)
                    return orig_setup(self)

                cls.setUp = setup_override
                # if cls.tearDown is not BaseTestCase.tearDown:
                #     orig_teardown = cls.tearDown
                #
                #     def teardown_override(self):
                #         """Overridden teardown method"""
                #         BaseTestCase.tearDown(self)
                #         return orig_teardown(self)
                #     cls.tearDown = teardown_override

    @classmethod
    def tearDownClass(cls):
        # clean up testing data if all tests passed
        if BaseTestCase.result and BaseTestCase.result.wasSuccessful():
            for path in BaseTestCase.data_paths:
                try:
                    shutil.rmtree(path, onerror=cls.__del_helper)
                except FileNotFoundError as e:
                    pass
                except Exception as e:
                    logging.exception(e)

    def run(self, result=None):
        # keep track of the latest test result
        if not result:
            result = self.defaultTestResult()
        BaseTestCase.result = result
        return unittest.TestCase.run(self, result)

    def setUp(self):
        # create shared folder if it doesn't exist
        os.makedirs(self.SHARED_PATH, exist_ok=True)

        # setup folder for the current test
        test_run = datetime.now().strftime("%Y%m%d_%H%M%S") + '_' + self.id()
        test_folder = os.path.join(BaseTestCase.INDIVIDUAL_PATH, test_run)
        os.makedirs(test_folder, exist_ok=True)
        self.data_path = test_folder
        if test_folder not in self.data_paths:
            self.data_paths.append(test_folder)

    @classmethod
    def __del_helper(cls, func, dir_path, exc):
        os.chmod(dir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(dir_path)

    def clear_data_path(self):
        """
        Clear application data path for running the current test case
        """
        for file in os.listdir(self.data_path):
            fname = os.path.join(self.data_path, file)
            try:
                if os.path.isfile(fname):
                    os.unlink(fname)
                elif os.path.isdir(fname):
                    shutil.rmtree(fname, onerror=self.__del_helper)
            except Exception as e:
                print(e)

    ###########################################################################
    # Assertions
    ###########################################################################
    def assertPathEqual(self, path1, path2, msg=None):
        self.assertEqual(
            os.path.normpath(path1),
            os.path.normpath(path2),
            msg
        )


class RandomData:
    ALPHANUM = string.ascii_letters + string.digits

    @staticmethod
    def string(len: int = 5) -> str:
        """
        Returns a random string of the given length
        """
        return ''.join(
                [random.choice(RandomData.ALPHANUM) for _ in range(len)])

    @staticmethod
    def boolean() -> bool:
        return bool(random.randint(0, 1))

    @staticmethod
    def system_update(planets: int = 0) -> PlanetarySysUpdate:
        sysupd = PlanetarySysUpdate(
                name=RandomData.string(),
                new=RandomData.boolean()
        )
        for i in range(planets):
            sysupd.planets.append(RandomData.planet_update())
        return sysupd

    @staticmethod
    def planet_update() -> PlanetUpdate:
        planetupd = PlanetUpdate(
                name=RandomData.string(),
                new=RandomData.boolean()
        )
        return planetupd
