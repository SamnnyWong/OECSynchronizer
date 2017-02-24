from abc import ABC, abstractmethod
from astro_unit import Quantity
from typing import List, Dict, Set
import re


class Body:
    """
    Model of a celestial body.
    """
    REGEX_ALPHA_NUM = re.compile(R"[^0-9a-z]*")

    def __init__(self,
                 name: str,
                 all_names: Set[str],
                 prop: Dict[str, Quantity]):
        """
        :param name: Name of the celestial body.
        """
        self.name = name

        all_names.add(name)
        self.all_names = frozenset(self.sanitize_name(n) for n in all_names)
        self.prop = prop  # properties

    def __eq__(self, other: 'Body'):
        """
        Return True if this body is the same as the other body. Regardless
        of the difference in the properties.
        :param other: The other celestial body.
        :return: Whether they represent the same body.
        """
        return not self.all_names.isdisjoint(other.all_names)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Body(%(name)r, %(all_names)r, %(prop)r)" % self.__dict__

    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Sanitizes a body name by removing non-alphanumeric characters,
        and convert to all-lowercase.
        :param name: Original name
        :return: Sanitized name
        """
        return Body.REGEX_ALPHA_NUM.sub("", name.lower())


class Planet(Body):
    """
    Model of a planet in any catalogue.
    """

    def __init__(self,
                 name: str,
                 system: str,
                 all_names: Set[str]=None,
                 prop: Dict[str, Quantity]=None):
        """
        :param name: Planet name.
        :param system: Host system.
        """
        all_names = all_names or set()
        prop = prop or dict()
        super().__init__(name, all_names, prop)
        self.system = system

    def __repr__(self):
        return "Planet(%(name)r, %(system)r, %(all_names)r, %(prop)r)" % \
               self.__dict__

    def __eq__(self, other: 'Planet'):
        return Body.__eq__(self, other) and self.system == other.system


class System(Body):
    """
    Model of a system in any catalogue.
    """

    def __init__(self,
                 name: str,
                 file: str=None,
                 planets: List[Planet]=None,
                 all_names: Set[str]=None,
                 prop: Dict[str, Quantity]=None):
        """
        Initialize a System object.
        :param name: Default name of the system
        :param file: File storing the system info
        :param planets: List of planets in the system
        :param all_names: Set of all names of this system
        :param prop: Properties of this system.
        """
        planets = planets or list()
        all_names = all_names or set()
        prop = prop or dict()
        super().__init__(name, all_names, prop)
        self.planets = planets
        self.file = file

    def __repr__(self):
        return "System(%(name)r, %(file)r, " \
               "%(planets)r, %(all_names)r, %(prop)r)" % \
               self.__dict__

    def update_planets(self, new_planet: Planet, old_planet: Planet=None):
        """
        Removes all old_planet by name, if any, and
        adds new_planet to the planets of this system.
        :param new_planet: New planet of this system
        :param old_planet: Existing planet, if any
        :return:
        """
        if old_planet:
            for index, planet in enumerate(self.planets):
                if planet.name == old_planet.name:
                    self.planets.pop(index)
        self.planets.append(new_planet)


class BodyUpdate(ABC):
    """
    Changes to the info of a celestial body.
    """
    @abstractmethod
    def __init__(self, name: str, new: bool=False):
        """
        :param name: Name of this celestial body.
        :param new: Is it new to OEC?
        """
        self.name = name
        self.new = new


class PlanetUpdate(BodyUpdate):
    """
    Updated planet info.
    """
    def __init__(self, name: str, new: bool=False,
                 fields: Dict[str, Quantity]=None):
        super().__init__(name, new)
        self.fields = fields if fields is not None else dict()

    def __repr__(self):
        return "PlanetUpdate(%(name)r, %(new)r, %(fields)r)" % \
            self.__dict__


class PlanetarySysUpdate(BodyUpdate):
    """
    Representation of all changes to planets inside the same planetary system.
    """
    def __init__(self, name: str, new: bool=False,
                 planets: List[PlanetUpdate]=None):
        super().__init__(name, new)
        self.planets = planets if planets is not None else list()

    def __repr__(self):
        return "PlanetarySysUpdate(%(name)r, %(new)r, %(planets)r)" % \
            self.__dict__

    def add_update(self, new_update: PlanetUpdate):
        """
        Adds new planet update to this planetary system update.
        :param new_update: New planet update
        :return: None
        """
        self.planets.append(new_update)
