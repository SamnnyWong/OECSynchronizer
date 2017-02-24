### `Synchronizer`
The integration of all the other components. It provides the interfaces to the front end:
- `sync`: it compares OEC with other catalogues and generate a list of changes grouped by systems
- `submit`: given changes to a single system, create a pull request to the OEC repository.
- `reject`: reject the changes to a system by creating then closing a pull request.

### `model`
This package defines the data models required by our application.

### `OECAdapter`
Stands between OEC and our class models. It is the class that handles the reading and writing of the XML system files in the OEC.

### `MonitoredCatalogue`
The object that stores the data (all the systems and planets) in a catalogue being monitored, such as NASA or Exoplanet.eu. It updates the data by downloading the csv file from the internet, then filter out unwanted columns and convert the rest into the format defined by our class models.

##### `CatalogueConfig`
This is the configuration that contains the information required to monitor a catalogue such as NASA. Once instantiated it will be corresponding to the a YAML file that is located under `oec_sync/sync_config`.

### `RepoManager`
This class interacts with the locally-cloned OEC repository. It implements the basic git commands such as:
- checking out a branch
- creating and deleting a branch
- creating a commit
- pushing a commit to the remote
- pulling a branch

### `UpdateRequest`
The representation of a request of changes to be made to a system. It contains the information about the changes itself, and additional information such as commit messages, corresponding github pull request. 

### `UpdateRequestDB`
This is a 'database' of `UpdateRequest`s that synchronizes with existing Github pull requests. It controls the creation of pull requests by monitoring (and caching) existing pull requests, and ensures that duplicate pull requests will not be submitted to the repository.

### `astro_unit` and `Quantity`
A `Quantity` object stores a number with its unit and uncertainties, so that it supports the conversion between units. The unit conversion is done via `pint` library, and an additional unit definition file at `oec_sync/sync/resources/units.txt`.
