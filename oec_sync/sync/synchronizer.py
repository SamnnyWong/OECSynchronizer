import os
import glob
from update_request import *
from repo_manager import *
from catalogue import *
import oec
from typing import Callable, Optional
from comparer import data_compare
from syncutil import SrcPath, Helper, ProgressCallback


class Synchronizer:
    """
    Synchronizes OEC with other catalogue by monitoring them and provides
    options to commit and/or create pull request about changes to OEC.
    """
    DATAPATH_OEC = 'oec'
    DATAPATH_REQUEST_CACHE = 'requests.db'
    DATAPATH_ROOT = '.oec-sync'

    # systems under 'systems' and 'systems_kepler' are overlapping.
    # for example, Kepler-386 == KOI-2442
    SYSTEM_PATHS = ['systems']  # , 'systems_kepler']

    def __init__(self, config_file: str, data_root: str=None):
        """
        :param config_file: Path to the synchronizer configuration file.
        :param data_root: Path to the local app data directory, will attempt
        creating one if it does not exist.
        """
        # load configuration
        config = Helper.read_conf(config_file)  # throws init error
        self.config = config
        self.data_root = data_root
        if not self.data_root:
            self.data_root = os.path.join(
                    os.path.expanduser('~'),
                    Synchronizer.DATAPATH_ROOT)
        if not os.path.exists(self.data_root):
            os.makedirs(self.data_root)  # make app folder if needed

        # initialize oec repository manager

        # embed the token into clone url (works only for HTTPS)
        oec_git_path = config['oec_git']
        oec_git_path = oec_git_path.replace('https://github.com',
                                            'https://%s:%s@github.com' %
                                            (config['gh_username'],
                                             config['gh_api_token']))
        self.oec_repo = RepoManager(
                self._datapath(Synchronizer.DATAPATH_OEC),
                oec_git_path)

        # create the adapter that manipulates oec files
        self.oec_adapter = oec.Adapter()

        # load oec into memory
        self.oec_system = dict()
        self._reload_oec()

        # initialize update request database
        self.db = UpdateRequestDB(
                self._datapath(Synchronizer.DATAPATH_REQUEST_CACHE),
                config['gh_api_token'],
                config['gh_repo'])

        # initialize list of monitored catalogues
        self.cats = []
        self._reload_cat_config()

    def sync(self, callback: Callable[[UpdateRequest], None],
             progress: ProgressCallback=None) -> None:
        """
        Get changes from monitored catalogue.
        :param callback: handler of new update request
        :param progress: handler of progress update event
        """
        update_progress = progress or (lambda a, b, c=None: True)

        # pull oec repository before sync
        self.oec_repo.checkout()
        self.oec_repo.pull()
        self._reload_oec()

        # synchronize existing update request with Github pull request
        self.db.fetch_all(progress=update_progress)

        # fetch latest catalogues
        update_progress(0, len(self.cats), "Fetching data...")
        sys_total = 0
        for cat_i, cat in enumerate(self.cats):
            logging.info('Fetching data from [%s]...' % cat.config.name)
            cat.fetch()

            sys_count = len(cat.systems)
            logging.info("Found %d systems in the catalogue" % sys_count)
            sys_total += sys_count

            update_progress(cat_i+1, len(self.cats))

        sys_processed = 0
        update_count = 0
        unknown_count = 0
        skip_count = 0

        for cat_idx, cat in enumerate(self.cats):
            logging.info('Syncing with [%s]...' % cat.config.name)

            for cat_sysname, system in cat.systems.items():
                oec_sys = self.oec_system.get(Body.sanitize_name(cat_sysname))
                # find the matching system in OEC
                if oec_sys is not None:
                    logging.debug("Analysing " + oec_sys.name)
                    sysupd = data_compare(oec_sys, system)
                    if sysupd is not None:
                        # found a change
                        req = UpdateRequest(sysupd, reference=cat.config.name)
                        # check for duplicates
                        similar_req = self.db.get_similar(req)
                        if similar_req is not None:
                            logging.info("Skipping update request to [%s]:"
                                         " similar to PR #%d (%s)"
                                         % (req.updates.name,
                                            similar_req.request.pullreq_num,
                                            similar_req.request.pullreq_url))
                            skip_count += 1
                        else:
                            callback(req)
                            update_count += 1
                else:
                    logging.debug('Unknown system "%s"' % cat_sysname)
                    unknown_count += 1

                # update progress
                sys_processed += 1
                update_progress(sys_processed, sys_total,
                                "Creating update requests locally...")

            logging.info("[%s] Done" % cat.config.name)

        logging.info("Sync completed:\n"
                     "Processed %d systems(s)\n"
                     "created %d update request(s) (+%d skipped)\n"
                     "found %d unknown system(s)\n" %
                     (sys_processed,
                      update_count, skip_count,
                      unknown_count))

    def get_system_file(self, system_name: str) -> str:
        """
        Locates a system file from the local oec repository.
        :param system_name: System name.
        :return: Path to the xml file representing the system.
        Returns None if the no such file exists.
        """
        system = self.oec_system.get(Body.sanitize_name(system_name))
        return system.file

    def submit(self,
               req: UpdateRequest,
               editor: Callable[[str], str]=None,
               force: bool=False) \
            -> int:
        """
        Submits an update request to OEC as a Github pull request.
        :param req: the update request
        :param editor: function that edits and returns the final content
        :param force: ignore duplicates
        :return: pull request id
        """
        filename = self.get_system_file(req.updates.name)
        if not filename:
            raise FileNotFoundError("Could not locate the system file")

        file_content = ''
        with open(filename, 'r') as f:
            file_content = f.read()

        # apply the update to the in-memory file content
        logging.info("Applying update to system [%s]" % req.updates.name)
        file_content, ok = self.oec_adapter.update_str(file_content,
                                                       req.updates)

        # allow human intervention here
        if editor:
            file_content = editor(file_content)
            if not file_content:
                logging.info("File is empty. Abort submission.")
                return

        # make sure there is newline at the end of file
        if file_content[-1] != '\n':
            file_content += '\n'

        def write_file():
            # overwrite the entire file, don't convert line endings
            with open(filename, 'w', newline='') as f:
                f.write(file_content)
            return True

        logging.info("Pushing update to remote branch '%s'" % req.branch)
        commit_hash = self.oec_repo.submit(req.get_summary(),
                                           req.branch,
                                           write_file)
        logging.debug("Commit hash: " + commit_hash)

        # submit pull request
        logging.info("Creating pull request...")
        self.db.submit(req, force)
        return req.pullreq_num

    def reject(self, req: UpdateRequest, force: bool=False):
        """
        Submits the update request to OEC, and closes it without merge
        :param req: the update request
        :param force: Ignore duplicates
        :return: pull request id
        """
        pullreq_num = self.submit(req, None, force)
        if pullreq_num:
            self.db.reject(req)
        return pullreq_num

    def _datapath(self, name: str = None):
        return os.path.join(self.data_root, name)

    def _reload_oec(self) -> None:
        """
        Reload OEC from local repository.
        """
        logging.info("Parsing OEC systems...")
        oec_path = self.oec_repo.root
        self.oec_system.clear()
        for system_path in Synchronizer.SYSTEM_PATHS:
            pattern = os.path.join(oec_path, system_path, '*.xml')
            for system_file in glob.glob(pattern):
                system = self.oec_adapter.read_system(system_file)

                # map all alternate names to this system object
                for sys_name in system.all_names:
                    if sys_name in self.oec_system:
                        # this means two different systems have the same name
                        logging.debug("Naming conflict between <%s> and <%s>"
                                      % (self.oec_system[sys_name].name,
                                         system.name))
                        continue
                    self.oec_system[sys_name] = system
                logging.debug("Loaded " + system_file)

    def _reload_cat_config(self) -> None:
        """
        Reload catalogue config files.
        """
        del self.cats[:]

        # TODO: they will be fetched from a git repo in the future
        pattern = SrcPath.abs(self.config['cat_config_path'], '*.yml')
        for f in glob.glob(pattern):
            try:
                with open(f, 'r') as fin:
                    cat_config = CatalogueConfig(fin)
                    cat = MonitoredCatalogue(cat_config)
                    self.cats.append(cat)
            except Exception as e:
                logging.error('Failed loading config "%s": %s' % (f, e))

        if len(self.cats) == 0:
            logging.warning('No catalogue configurations found in "%s".' %
                            pattern)
