import requests
import csv
from typing import Any
import logging
import yaml
import oec
from io import StringIO
from model import *
from syncutil import SrcPath


class CatalogueConfig:
    """
    Configuration for a monitored catalogue.
    """

    def __init__(self, stream):
        """
        :param stream: an opened yaml file
        """
        self.raw = yaml.load(stream)
        ignored = self.raw.get('ignore')
        if ignored:
            raise ValueError('config is ignored')

        self.name = self.__get_or_fail('name')

        self.url = self.__get_or_fail('url')
        self.system_name = self.__get_or_fail('system_name')

        self.planet_name = self.raw.get('planet_name')
        self.planet_letter = self.raw.get('planet_letter')
        if not self.planet_name and not self.planet_letter:
            raise ValueError('empty planet_name and planet_letter')

        self.field_map = self.__get_or_fail('field_map')

        # validate field mappings
        for k, v in list(self.field_map.items()):
            errors = []

            if k not in oec.PLANET_FIELDS:
                errors.append('field is not monitored in OEC')

            oec_field = oec.PLANET_FIELDS[k]
            if type(v) is dict:
                if 'name' not in v:
                    errors.append('Missing "name" key')
                if (oec_field.unit is None) == ('unit' in v):
                    errors.append('OEC and monitored catalogue must both '
                                  'have unit defined')
            if errors:
                logging.error(
                    ('Ignored mapping "%s": \n\t' % k) +
                    '\n\t'.join(errors)
                )
                del self.field_map[k]
                continue
            logging.debug('Read mapping: %s' % k)

        # self.value_map = self._raw['value_map']    # ignore this for now

    def __get_or_fail(self, key: str) -> Any:
        value = self.raw[key]
        if not value:
            raise ValueError('empty value for key "%s"' % key)
        return value


class MonitoredCatalogue:
    """
    # download csv file
    # retrieved montinored catalogue field from synchronizer
    # filter our unwanted field
    # convert all the value into oec form (Str convert and unit convert)
    # output a list of planet object

    The exoplanet data from a monitored catalogue,
    such as NASA Exoplanet Archive
    """
    def __init__(self, config: CatalogueConfig):
        """
        :param config: The configuration for this monitored catalogue.
        """
        self.config = config
        self.systems = None  # dict of System

    def fetch(self) -> None:
        """
        Fetch the latest csv from monitored catalogue
        """
        reader = None

        # debug feature - load file locally
        debug_file = self.config.raw.get('debug_file')
        if debug_file:
            debug_file = SrcPath.abs(debug_file)
            with open(debug_file, 'r') as f:
                # read the entire file so we can close it right away
                reader = csv.DictReader(StringIO(f.read()))
                logging.debug("Loaded catalogue from local debug file")

        if not reader:
            f = requests.get(self.config.url)
            result = f.text
            reader = csv.DictReader(StringIO(result))

        # search the index of required field in raw field list
        # self._search_index(raw_col)
        # loop through each row in the csv

        self.systems = dict()

        def try_get_field(row: Dict[str, str], fielddesc: Dict[str, str],
                          oec_field_name: str):
            cat_field_name = fielddesc.get(oec_field_name)
            if cat_field_name:
                row_value = row.get(cat_field_name)
                return row_value

        for next_planet in reader:
            system_name = next_planet[self.config.system_name]

            planet_name = None
            if self.config.planet_name:
                planet_name = next_planet[self.config.planet_name]
            else:
                planet_name = system_name + ' ' +\
                              next_planet[self.config.planet_letter]

            pl = Planet(planet_name, system_name)

            for oec_field, cat_fieldmeta in self.config.field_map.items():
                value = next_planet.get(cat_fieldmeta['name'])
                if value:
                    errorminus = try_get_field(next_planet,
                                               cat_fieldmeta, 'errorminus')
                    errorplus = try_get_field(next_planet,
                                              cat_fieldmeta, 'errorplus')
                    lowerlimit = try_get_field(next_planet,
                                               cat_fieldmeta, 'lowerlimit')
                    upperlimit = try_get_field(next_planet,
                                               cat_fieldmeta, 'upperlimit')
                    limitflag = try_get_field(next_planet,
                                              cat_fieldmeta, 'limit_flag')

                    explicit_limit = lowerlimit or upperlimit

                    errors = (lowerlimit, upperlimit)\
                        if explicit_limit else (errorminus, errorplus)

                    q = Quantity(
                        value,
                        cat_fieldmeta.get('unit'),
                        errors,
                        bool(explicit_limit or (limitflag is None and
                                                bool(limitflag)))
                    )

                    # convert the quantity if it's using different unit
                    oec_fieldmeta = oec.PLANET_FIELDS[oec_field]
                    if oec_fieldmeta.unit != cat_fieldmeta.get('unit'):
                        q = q.to(oec_fieldmeta.unit)
                    pl.prop[oec_field] = q

            sys = self.systems.get(system_name)
            if sys is None:
                self.systems[system_name] = sys = System(system_name)
            sys.planets.append(pl)

    def _value_convert(self):
        pass

    def _unit_convert(self):
        pass
