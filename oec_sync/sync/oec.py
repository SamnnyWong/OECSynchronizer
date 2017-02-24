from xml.etree import ElementTree as Etree
from model import *
from astro_unit import *
from io import StringIO
import logging


class FieldMeta:
    """
    OEC field metadata.
    """
    def __init__(self, datatype: str, unit: str = None):
        self.type = datatype
        self.unit = unit


# Maps field name to tuple of (type, unit)
# Only the following columns will be understood
PLANET_FIELDS = {
    "semimajoraxis": FieldMeta("number", 'AU'),
    "eccentricity": FieldMeta("number"),  # unit not needed
    "periastron": FieldMeta("number", 'deg'),
    "longitude": FieldMeta("number", 'deg'),
    "ascendingnode": FieldMeta("number", 'deg'),
    "inclination": FieldMeta("number", 'deg'),
    "impactparameter": FieldMeta("number"),  # unit not needed
    "meananomaly": FieldMeta("number", 'deg'),
    "period": FieldMeta("number", 'days'),
    "transittime": FieldMeta("number", 'BJD'),
    "periastrontime": FieldMeta("number", 'BJD'),
    "maximumrvtime": FieldMeta("number", 'BJD'),
    "separation": FieldMeta("number", 'arcsec'),  # unit on xml element
    "mass": FieldMeta("number", 'M_j'),
    "radius": FieldMeta("number", 'R_j'),
    "temperature": FieldMeta("number", 'K'),
    "age": FieldMeta("number", 'Gyr'),
    # "discoverymethod": FieldMeta("discoverymethodtype"),
    # "istransiting": FieldMeta("boolean"),
    # "description": "xs:string",
    "discoveryyear": FieldMeta("number", None),
    # "lastupdate": FieldMeta("lastupdatedef", None),
    # "image",
    # "imagedescription",
    "spinorbitalignment": FieldMeta("number", 'deg'),
    "positionangle": FieldMeta("number", 'deg'),
    # "metallicity": FieldMeta("number"),  # unit not needed
    # "spectraltype": FieldMeta("spectraltypedef"),
    # "magB": FieldMeta("number", None),
    "magH": FieldMeta("number", None),
    "magI": FieldMeta("number", None),
    "magJ": FieldMeta("number", None),
    "magK": FieldMeta("number", None),
    # "magR": FieldMeta("number", None),
    # "magU": FieldMeta("number", None),
    "magV": FieldMeta("number", None)
}


class Adapter:
    """
    Reads/writes OEC files.
    """
    def __init__(self, schema_file: str=None):
        """
        :param schema_file: Schema file (*.xsd)
        """
        # process schema
        if schema_file:
            self._schema_tree = Etree.parse(schema_file).getroot()

    @staticmethod
    def _read_number(field: Etree.Element, fieldmeta: FieldMeta)\
            -> Quantity:
        # read unit
        unit = fieldmeta.unit
        if unit is None:        # check if element has unit defined
            unit = field.get('unit')

        # read limits/errors
        lower, upper = field.get('lowerlimit'), field.get('upperlimit')
        is_limit = bool(lower or upper)
        if not is_limit:
            lower, upper = field.get('errorminus'), field.get('errorplus')

        q = Quantity(field.text, unit, error=(lower, upper), is_limit=is_limit)
        return q

    @staticmethod
    def _read_planet(root: Etree.Element, system_name: str) -> Planet:
        """
        Reads out a planet from an xml element.
        :param root: Must be a planet element.
        :param system_name: System name.
        :return: Planet object.
        """
        if root.tag != 'planet':
            raise NameError('Root must be a planet element')
        default_name = root.find('name').text
        if not default_name:
            raise SyntaxError('Could not find planet name')

        all_names = set(name.text for name in root.findall('name'))
        planet = Planet(default_name, system_name, all_names=all_names)
        for field in next(root.iter()):
            fieldmeta = PLANET_FIELDS.get(field.tag)
            if fieldmeta:
                try:
                    # Some OEC files are weird
                    # e.g. KOI-12.xml, line 27 is
                    # 			<mass upperlimit="8.7" />
                    if fieldmeta.type == "number":
                        planet.prop[field.tag] = \
                            Adapter._read_number(field, fieldmeta)
                    else:
                        planet.prop[field.tag] = field.text
                except ValueError as e:
                    logging.debug("[%s].[%s]: %s" %
                                  (default_name, field.tag, e))
                except Exception as e:
                    logging.exception(e)
        return planet

    def read_system(self, file: str) -> System:
        """
        Reads out planets in a system.
        :param file: Path to a system xml file.
        :return: A list of planets.
        """
        tree = Etree.parse(file)

        root = tree.getroot()
        if root.tag != 'system':
            raise NameError('Root must be a system element')

        all_names = set(name.text for name in root.findall('name'))
        system = System(root.find('name').text, file, all_names=all_names)

        for planet_xml in root.iter('planet'):
            planet = self._read_planet(planet_xml, system.name)
            system.planets.append(planet)
        return system

    @staticmethod
    def _write_number(field: Etree.Element, number: Quantity) -> bool:
        # attrib is a dictionary holding the attributes of this element
        attrib = field.attrib

        # silently clear existing error terms
        attrib.pop('errorminus', None)
        attrib.pop('errorplus', None)
        attrib.pop('lowerlimit', None)
        attrib.pop('upperlimit', None)

        # set new value
        field.text = number.value

        # set new error terms
        if number.error:
            if number.is_limit:
                attrib['lowerlimit'], attrib['upperlimit'] = number.error
            else:
                attrib['errorminus'], attrib['errorplus'] = number.error
        return True

    @staticmethod
    def _write_planet_update(planet: Etree.Element, update: PlanetUpdate) \
            -> bool:
        succeeded = True
        # loop through new values in the update objects
        for field, new_value in update.fields.items():
            try:
                prop_elem = planet.find(field)
                if prop_elem is None:
                    # the original planet does not have this field
                    logging.debug("Creating new field '%s'" % field)
                    # create the field under the planet
                    prop_elem = Etree.SubElement(planet, field)

                # write the new value
                succeeded &= Adapter._write_number(prop_elem, new_value)
            except Exception as e:
                logging.exception(e)
                succeeded = False
        return succeeded

    @staticmethod
    def _write_system_update(root: Etree.Element,
                             update: PlanetarySysUpdate) -> bool:
        if update.new:
            # a new system?
            raise NotImplementedError

        succeeded = True
        for planet_update in update.planets:
            if planet_update.new:
                succeeded = False
                logging.debug('Skipped new planet update %r' % planet_update)
                continue

            # find planet element with the name
            planet_elem = root.find('.//planet[name="%s"]' %
                                    planet_update.name)

            # planet does not exist in the file?
            # creating a new planet isn't as easy,
            # need some info about the host star.
            if planet_elem is None:
                succeeded = False
                logging.debug('Could not find planet <%s>' %
                              planet_update.name)
                continue

            # apply the update to the current planet
            logging.debug('Updating planet <%s>...' %
                          planet_update.name)
            succeeded &= Adapter._write_planet_update(
                    planet_elem,
                    planet_update)
        return succeeded
    # def validate(self, file: str) -> None:
    #     Validates an xml using schema defined by OEC.
    #     Raises an exception if file does not follow the schema.
    #     :param file: File name.
    #     """
    #     return  # skip for now, because OEC itself isn't following the schema
    #     # tree = etree.parse(file)
    #     # self._schema.assertValid(tree)

    def update_str(self, xml_string: str, update: PlanetarySysUpdate) \
            -> Tuple[str, bool]:
        """
        Apply a system update to an xml string.
        Also performs a check afterwards to determine if
        the action succeeded.
        :param xml_string: containing the xml representation of a system
        :param update: Update to be applied to the system
        :return: A tuple (content, succeeded) where:
            - content is the file content modified
            - succeeded indicates whether the update was successful.
        """
        tree = Etree.parse(StringIO(xml_string))
        ok = Adapter._write_system_update(tree, update)
        serialized = Etree.tostring(tree.getroot(), 'unicode', 'xml')
        return serialized, ok

    def update_file(self, filename: str, update: PlanetarySysUpdate) -> bool:
        """
        Apply a system update to an xml file.
        :param filename: The system xml file
        :param update: Update to be applied to the system
        :return: Whether the update was successful
        """
        tree = Etree.parse(filename)
        succeeded = Adapter._write_system_update(tree, update)
        tree.write(filename)
        return succeeded
