import shelve
import requests
import io
import re
import uuid
import logging
import enum
import time
import json
import hashlib
from datetime import datetime
from typing import Tuple, Union, Any
from github import Github, UnknownObjectException
from github.PullRequest import PullRequest

from model import PlanetarySysUpdate
from syncutil import ProgressCallback
from comparer import data_compare
import oec


class FormatError(ValueError):
    """
    Indicates an update request has an invalid format.
    """
    def __init__(self, msg: str):
        super().__init__(msg)


class ReconstructionError(Exception):
    """
    Error occurred during the reconstruction of update request
    from a pull request.
    """
    def __init__(self, msg: str):
        super().__init__(msg)


@enum.unique
class IgnoredRequest(enum.Enum):
    """
    Enum of types of pull requests that are permanently ignored.
    """
    # request has been approved and merged
    # this is irreversible, so we can safely ignore it in the future
    merged = 1

    # possible cases where pull request is invalid:
    # - changes multiple files
    # - changes no files
    # - changes non system files
    # the content of the pull request may change (and become valid!),
    # but for simplicity's sake we will just ignore them
    invalid = 2


class UpdateRequest:
    """
    An update request.
    """
    # The URL to download a file at a specific commit
    FILE_URL = 'https://raw.githubusercontent.com/{repo}/{commit}/{file}'

    def __init__(self,
                 updates: PlanetarySysUpdate,
                 title: str=None,
                 message: str=None,
                 reference: str=None,
                 pullreq_num: int=0,
                 pullreq_url: str=None,
                 branch: str=None,
                 rejected: bool=False):
        """
        Construct from an update to a planetary system.
        :param updates: The update object.
        """
        self.updates = updates

        # request title, part of commit message
        self.title = title or ('Update ' + self.updates.name)

        # user-defined message
        self.message = message

        # reference to data source, e.g. 'NASA'
        self.reference = reference

        # pull request number
        self.pullreq_num = pullreq_num

        # branch name
        self.branch = branch

        # link to the pull request page
        self.pullreq_url = pullreq_url

        # is the pull request rejected
        self.rejected = rejected

        # initialization for local update requests
        if pullreq_num == 0:
            self.branch = self._gen_branch_name()

    def __str__(self):
        return "#%(pullreq_num)s %(title)s" % self.__dict__

    @classmethod
    def from_pull_request(cls, pr: PullRequest) \
            -> Union['UpdateRequest', IgnoredRequest]:
        """
        Construct from a Github pull request.
        :param pr: The pull request.
        :return: The constructed update request.
        """
        if pr.is_merged():
            return IgnoredRequest.merged

        if pr.changed_files != 1:
            return IgnoredRequest.invalid
        
        # system file after merge
        file = pr.get_files()[0]

        # construct download url of the original file
        orig_file = cls.FILE_URL.format(
            repo=pr.base.repo.full_name,
            commit=pr.base.sha,
            file=file.filename
        )

        # retrieve the original and patched files
        resp = requests.get(orig_file)
        if not resp.ok:
            raise ReconstructionError('Unable to retrieve the original file: '
                                      '%d %s' % (resp.status_code,
                                                 resp.reason))
        original = resp.text

        resp = requests.get(file.raw_url)
        if not resp.ok:
            raise ReconstructionError('Unable to retrieve the original file: '
                                      '%d %s' % (resp.status_code,
                                                 resp.reason))
        patched = resp.text

        # read xml and reconstruct system update object
        update = None
        try:
            adapter = oec.Adapter()
            update = data_compare(
                    adapter.read_system(io.StringIO(original)),
                    adapter.read_system(io.StringIO(patched))
            )
            if update is None:
                logging.debug('No changes detected on ' + pr.number)
                return IgnoredRequest.invalid
        except Exception as e:
            logging.debug(e)
            return IgnoredRequest.invalid

        message, reference = UpdateRequest._parse_description(pr.body)
        return UpdateRequest(
                update,
                title=pr.title,
                message=message,
                reference=reference,
                pullreq_num=pr.number,
                pullreq_url=pr.html_url,
                branch=pr.head.label,
                rejected=pr.state == "closed"
        )

    def _gen_branch_name(self) -> str:
        date = datetime.utcnow().strftime('%Y%m%d')
        sysname = self._sanitize_branch_name(self.updates.name)
        uid = uuid.uuid4().hex
        return '_'.join((date, sysname, uid))

    @staticmethod
    def _sanitize_branch_name(name: str) -> str:
        """
        Santize a branch name. Keep only lowercase letters and digits
        :param name: Unsanitized branch name
        :return: Sanitized branch name
        """
        # split on anything other than alphanumerics and dashes
        return '-'.join(re.split(r'[^\w\d-]+', name.lower()))

    @staticmethod
    def _parse_description(message: str) -> Tuple[str, str]:
        """
        Extracts user message and reference from the pull request message.
        :param message: The pull request message.
        :return: A tuple of (user message, reference)
        """
        ref = None
        usermsg_lines = []
        for line in message.splitlines():
            line = line.strip()
            if not line:
                continue

            # try parsing reference text
            match_ref = re.match('(Reference:).*', line)
            if match_ref:
                ref = line[match_ref.end(1):].strip()
                break  # text after reference line will be ignored

            # otherwise, treat line as part of user message
            usermsg_lines.append(line)
        return '\n'.join(usermsg_lines), ref

    def get_summary(self) -> str:
        """
        :return: A summary message of this request.
        """
        if not self.reference:
            raise FormatError("Reference cannot be empty")

        # construct description text
        desc_parts = []
        if self.message:
            desc_parts.append(self.message)
        desc_parts.append('Reference: ' + self.reference)

        # format summary
        return '{0}\n\n{1}'.format(self.title, '\n'.join(desc_parts))


class CachedRequest:
    """
    Cached update request. Just an update request with digest value.
    Collision is possible, need to check equivalence later.
    """
    def __init__(self, req: UpdateRequest):
        assert req.pullreq_num > 0
        self.request = req
        self.checksum = CachedRequest.get_checksum(req)

    @staticmethod
    def get_checksum(req: UpdateRequest) -> str:
        """
        Computes the checksum of an update request
        :param req: the update request
        :return: the md5 checksum
        """
        dump = json.dumps(req.updates,
                          default=lambda o: o.__dict__,
                          sort_keys=True)
        return hashlib.md5(dump.encode('utf-8')).hexdigest()


class DuplicateError(Exception):
    """
    Indicates a local update request is a duplicate
    of an existing pull request.
    """
    def __init__(self, pr_num: int):
        self.pull_request_num = pr_num


class UpdateRequestDB:
    """
    The database of all update requests.
    """

    # minimum time until cache is refreshed
    MIN_CACHE_LIFETIME = 180 * 60    # seconds

    def __init__(self, cache_file: str, api_token: str, repo_name: str):
        """
        Loads the database into memory, from (Github and cache file).
        :param cache_file: Path to the cache file.
        :param api_token: Github API token.
        """
        self.github = Github(api_token)
        self.user = self.github.get_user()

        logging.info("Logged in as '%s' (%s)" % (self.user.login,
                                                 self.user.html_url))
        self.repo = self.github.get_repo(repo_name, lazy=False)
        logging.info("Repository found: '%s' (%s)" % (self.repo.full_name,
                                                      self.repo.html_url))

        self.requests = shelve.open(cache_file, writeback=True)

        # validate cache
        if len(self.requests) == 0:
            self.__init_db()
        elif not self.__validate_db():
            logging.info("Invalidating cache...")
            self.requests.clear()
            self.__init_db()

        logging.info("Building request lookup table...")
        self.__request_lookup = dict()
        for num, req in self.requests.items():
            if isinstance(req, CachedRequest):
                self.__request_lookup[req.checksum] = req

    def __del__(self):
        self.requests.close()

    def get_similar(self, req: UpdateRequest) -> CachedRequest:
        """
        Find similar requests in cache.
        :param req: a local update request
        :return: similar cached update request, if any.
        """
        # compute checksum
        req_checksum = CachedRequest.get_checksum(req)
        # find existing requests
        return self.__request_lookup.get(req_checksum)

    def __init_db(self):
        logging.info("Initializing cache...")
        self.__set_meta('repo', self.repo.full_name)
        self.requests.sync()

    def __get_meta(self, key: str) -> Any:
        return self.requests.get("META:"+key)

    def __set_meta(self, key: str, value: Any):
        self.requests["META:"+key] = value

    def __validate_db(self) -> bool:
        repo_name = self.__get_meta("repo")
        if not repo_name:
            logging.debug("Missing repo name")
            return False

        # check if repository names match
        if repo_name != self.repo.full_name:
            logging.debug("Repo changed from [%s] to [%s]"
                          % (repo_name, self.repo.full_name))
            return False

        # check value types
        meta_count = 0
        ignored_count = 0
        valid_count = 0
        for key, value in self.requests.items():
            if key.startswith("META:"):
                meta_count += 1
                continue
            if isinstance(value, IgnoredRequest):
                ignored_count += 1
                continue
            if isinstance(value, CachedRequest):
                valid_count += 1
                continue
            logging.debug("Unknown item: %s -> %s" % (key, value))
            return False

        logging.info("Cache validatd: "
                     "%d metadata, "
                     "%d requests, "
                     "%d ignored." %
                     (meta_count, valid_count, ignored_count))
        return True

    def __cache_pull_request(self, pull: PullRequest) -> CachedRequest:
        """
        Puts pull request into cache.
        """
        try:
            pull_num = str(pull.number)

            # Create cached request from pull request
            req = UpdateRequest.from_pull_request(pull)

            # Update requests need to be specially handled
            if isinstance(req, UpdateRequest):
                req = CachedRequest(req)
                original = self.requests.get(pull_num)
                if original is not None:
                    # remove lookup item of the old pull request
                    if isinstance(original, CachedRequest):
                        if original.checksum in self.__request_lookup:
                            del self.__request_lookup[original.checksum]
                # Update lookup table
                self.__request_lookup[req.checksum] = req

            # Add into db
            self.requests[pull_num] = req

        except ReconstructionError as e:
            # usually a network problem
            logging.debug(e)

    def submit(self, req: UpdateRequest, force: bool=False):
        """
        Submits an update request to Github.
        If succeeded update the pull request into the update request object
        :param req: The request to be submitted.
        :param force: Ignore duplicates.
        """
        assert req.branch is not None and req.branch != ""
        assert req.pullreq_num == 0
        assert req.pullreq_url is None

        # Check for duplicates
        if not force:
            self.fetch_all()
            similar_req = self.get_similar(req)
            if similar_req is not None:
                raise DuplicateError(similar_req.request.pullreq_num)

        # Submit the pull request
        pr = self.repo.create_pull(title=req.title,
                                   body=req.get_summary(),
                                   head=req.branch,
                                   base="master")
        if not pr:
            logging.info("Failed to created pull request")
            return

        req.pullreq_num = pr.number
        req.pullreq_url = pr.html_url
        logging.info("Created pull request #%d (%s)" %
                     (pr.number, pr.html_url))
        self.fetch_one(pr.number)

    def reject(self, req: UpdateRequest):
        """
        Closes an open pull request
        :param req: The update request with an open pull request
        """
        pr = self.repo.get_pull(req.pullreq_num)
        if pr:
            pr.edit(state="closed")
            req.rejected = True
            logging.info("Rejected pull request #%d" % pr.number)

    def fetch_all(self,
                  force_full_sync=False,
                  progress: ProgressCallback=None):
        """
        Gets the list of all pull requests from github, and store
        it in self.requests as a dictionary of
        pull request number -> CachedRequest object

        We have two modes of synchronization:
        - Full Sync:    Refresh all new/open requests.
                        This will happen if an amount of time has elapsed
                        since the last full sync.
        - Partial Sync: Don't refresh the cached requests, but keep an eye on
                        the newly added (open/closed) pull requests.

        :param force_full_sync: Do a full sync, ignore last synchronized time.
                     if set to false, will only discover new update requests.
        :param progress
        """
        update_progress = progress or (lambda a, b, c=None: True)

        # check if there's need to do a full sync
        full_sync = True
        if not force_full_sync:
            timestamp = self.__get_meta("last_full_sync")
            now = time.time()
            if timestamp is not None:
                if 0 < (now - timestamp) < self.MIN_CACHE_LIFETIME:
                    logging.debug("Partial Sync: Last synced on %f"
                                  % timestamp)
                    full_sync = False
                else:
                    logging.debug("Full Sync: Last synced on %f"
                                  % timestamp)

        # set of pull request numbers fetched this time
        just_fetched = set()

        # find open pull requests
        max_pr_number = 1
        if full_sync:
            update_progress(0, 1, "Check for pending requests...")
            pulls = self.repo.get_pulls("open")
            for pull_idx, pull in enumerate(pulls):

                update_progress(pull_idx, 100)

                max_pr_number = max(max_pr_number, pull.number)
                self.__cache_pull_request(pull)
                just_fetched.add(pull.number)
            update_progress(1, 1)

        # Ensure all pull requests are cached.
        # Also keep track of state of the previously open pull requests.
        # These are the transitions we need to pay attention to:
        # was open -> [merged|closed]
        update_progress(0, max_pr_number, "Fetching new requests...")
        pr_n = 0
        while pr_n < 1e5:
            pr_n += 1
            pull_request_num = str(pr_n)
            update_progress(pr_n, max_pr_number)

            if pr_n in just_fetched:
                continue

            ur = self.requests.get(pull_request_num)
            if ur is not None:
                if not full_sync:
                    # partial sync will skip as long as it's in cache
                    continue

                # pull request was marked as ignored
                if isinstance(ur, IgnoredRequest):
                    continue
                elif isinstance(ur, UpdateRequest):
                    if ur.rejected:
                        continue

            # otherwise, need to check for update to the pull request
            try:
                self.fetch_one(pr_n)
                just_fetched.add(pr_n)
            except UnknownObjectException:
                # no such pull request - iteration is complete
                break

        update_progress(pr_n, pr_n)
        logging.info("Sync complete: updated %d item(s)" %
                     len(just_fetched))
        if full_sync:
            self.__set_meta("last_full_sync", time.time())

        # commit changes
        self.requests.sync()

    def fetch_one(self, pull_request_num: int):
        """
        Fetch a single update request.
        :param pull_request_num: associated pull request number.
        """
        pull = self.repo.get_pull(pull_request_num)
        self.__cache_pull_request(pull)

        # commit changes
        self.requests.sync()
