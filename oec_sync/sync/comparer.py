from typing import Optional
from model import *


def data_compare(old_sys: System, new_sys: System) \
        -> Optional[PlanetarySysUpdate]:
    """
    :param old_sys: (list of dict of planet)
    :param new_sys: (list of dict of planet)
    :return: Changes to be made to the OEC system,
             or None if there is nothing to change.
    """
    if len(old_sys.planets) != 0 and len(new_sys.planets) != 0:
        update_sys = PlanetarySysUpdate(old_sys.name, False, [])
        # loop through list of planets
        for new_pl in new_sys.planets:
            if new_pl in old_sys.planets:
                old_pl = old_sys.planets[old_sys.planets.index(new_pl)]
                update_planet = PlanetUpdate(old_pl.name, False, {})
                # loop through fields in the newer planet
                for field, new_value in new_pl.prop.items():
                    # compare with fields in the old planet
                    old_value = old_pl.prop.get(field)
                    should_update = False
                    if not old_value:
                        # CASE: old planet doesn't have the field
                        should_update = True
                    elif old_value != new_value:
                        # CASE: new value
                        should_update = True
                    elif old_value.can_update_error(new_value):
                        # CASE: same value, different errors
                        should_update = True

                    # make the decision
                    if should_update:
                        update_planet.fields[field] = new_pl.prop[field]
                if update_planet.fields:
                    update_sys.add_update(update_planet)
            # if the planet in new system is not in old system
            else:
                new_added_planet = PlanetUpdate(new_pl.name, True, {})
                # add all fields into update
                new_added_planet.fields.update(new_pl.prop)
                # add planet update into the current system update
                update_sys.add_update(new_added_planet)
        if len(update_sys.planets) != 0:
            return update_sys
        return None
    else:
        return None
