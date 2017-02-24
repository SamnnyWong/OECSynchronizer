from os import path, chmod
from shutil import rmtree
from dulwich import porcelain, errors
from typing import Callable
import urllib
import logging
import git
import stat
'''
Using porcelain and git. Due to memory leak, this should be used in a
separate thread that only runs for as long as needed for the initialization
 or other stuff
'''


class RepoManager:
    """
    Manages a local copy of OEC repository.
    """
    REPO_BANNER = "OEC_SYNC REPOSITORY"

    def __init__(self, root: str, repository: str):
        """
        Initialize the manager for local OEC git repository.
        :type repository: str
        :param root: Path to the local repository.
        :param repository: Git clone path.
        """
        logging.info("__init__: Execution started")
        self.oec = None
        self.root = ""
        self.__remote = None
        self.__destroyed = True
        # convert ssh path to http and verify. Path verification is left to OS
        if repository[0:4] == 'git@':
            parts = repository.split(sep=":")
            repository = "https://github.com/" + parts[1]
        else:
            parsed_url = urllib.parse.urlparse(repository)
            if (parsed_url.scheme != "https" or
                    parsed_url.path[-4:] != '.git'):
                logging.error("Invalid repository URL")
                logging.info("__init__: Execution terminated")
                return

        logging.info("Verified URL")

        # Check app folder for a local copy of OEC repository. Delete and
        # re-init if necessary.
        # throw on error - probably need error handling class

        if path.isdir(root):
            try:
                # fetch an object to work with
                self.oec = git.Repo(root)
                if self.oec.description == self.REPO_BANNER:
                    if self.oec.is_dirty():
                        logging.warning("Repository contains modifications")
                        logging.warning("Resetting repository...")
                        self.destroy()
                    else:
                        self.root = root
                        self.__remote = self.oec.remote('origin')
                        self.__destroyed = False
                        logging.info("Repo initialized successfully")
                        logging.info("__init__: Execution terminated")
                        return
                else:
                    logging.info(root +
                                 " is not empty and is not an OEC repository")
                    logging.error("repository initialization failed."
                                  " InvalidGitRepository")
                    logging.info("__init__: Execution terminated")
                    return
            except git.exc.InvalidGitRepositoryError as e:
                logging.info(root +
                             " is not empty and is not an OEC repository")
                logging.error("repository initialization failed."
                              " InvalidGitRepository")
                logging.info("__init__: Execution terminated")
                return

        # clone repository to file system and set fields
        try:
            # clone the oec repo
            self.oec = git.Repo.clone_from(repository, root)
            # create a reference for remote ops like push pull etc
            self.__remote = self.oec.remote('origin')
            self.root = root
            # set the description so we can recognise it in future
            with open(path.join(self.root, '.git', 'description'), 'w')\
                    as description:
                description.write(self.REPO_BANNER)
            self.__destroyed = False
            logging.info("Repo initialized successfully")
            # attempt to checkout master
            self.checkout()
            # attempt to delete all the local branches
            self.delete_branch()
        except git.exc.GitCommandError as e:
            logging.error(e.stderr)
            self.destroy()
        logging.info("__init__: Execution terminated")
        return

    def checkout(self, branch_name: str='master') -> bool:
        """
        Checks out the specified branch.
        :param branch_name: Branch name.
        """
        logging.info("checkout: Execution started")
        checkout_success = False
        if self.__destroyed is not True:
            try:
                for indx in range(0, len(self.oec.branches)):
                    if self.oec.branches[indx].name == branch_name:
                        found_idx = indx
                        self.oec.refs[found_idx].checkout()
                        logging.info("Checkout successful")
                        checkout_success = True
                        break
                if not checkout_success:
                    logging.warning("No such branch '"
                                    + branch_name + "' exists")
            except git.exc.GitCommandError as e:
                logging.error("Unable to checkout branch " + branch_name)
                logging.error(e.stderr)
        logging.info("checkout: Execution terminated")
        return checkout_success

    def commit(self, commit_message: str) -> str:
        """
        Commit changes to the current branch.
        :param commit_message: Commit message.
        :return: Commit hash. Empty string if error occurred
        """
        # parse Update Request object and set related object fields
        logging.info("commit: Execution started")
        commit_hash = ""
        try:
            if self.__destroyed is not True:
                porcelain.add(self.root)
                commit_hash = porcelain.commit(
                      self.root, bytes(commit_message, 'utf-8')).decode()
                logging.info("Commit successful")
        except errors.CommitError:
            logging.error("Unable to commit update request: " +
                          commit_message)
        logging.info("Execution terminated")
        return commit_hash

    def branch(self, name: str) -> str:
        """
        Create a branch using the given name. Branch names MUST always be
         unique
        :param name: Suggested name of the branch.
        :return: Name of the created branch. Empty if error occurred
        """
        logging.info("branch: Execution started")
        created_branch = ""
        if self.__destroyed is not True:
            try:
                self.oec.refs.master.checkout(b=name, t=True)
                logging.info("branch " + name +
                             " has been created on repo self.oec")
                created_branch = name
            except git.exc.GitCommandError as e:
                logging.error("Error occurred while creating branch "
                              + name)
                logging.error(e.stderr)
        logging.info("branch: Execution terminated")
        return created_branch

    def push(self, branch_name: str) -> bool:
        """
        Push a branch to the remote, (and possibly delete the local one as we
                                      no longer need it).
        :param branch_name: Branch name.
        :return: If the branch 'branch_name' was successfully pushed
        """
        logging.info("push: Execution started")
        push_success = False
        if self.__destroyed is not True:
            try:
                for indx in range(0, len(self.oec.branches)):
                    if self.oec.branches[indx].name == branch_name:
                        self.__remote.push(self.oec.branches[indx])
                        logging.info("Push successful")
                        push_success = True
                        break
                if not push_success:
                    logging.error("No such branch '" + branch_name +
                                  "' exists")
            except git.exc.GitCommandError as e:
                logging.error("Unable to push branch " + branch_name)
                logging.error(e.stderr)
        logging.info("push: Execution terminated")
        return push_success

    def pull(self) -> None:
        """
        Pull the master branch.
        :return Whether the pull was successful
        """
        logging.info("pull: Execution started")
        pull_success = False
        if self.__destroyed is not True:
            try:
                # switch to master branch and pull
                self.checkout()
                self.__remote.pull()
                pull_success = True
            except git.exc.GitCommandError as e:
                logging.error("Unable to push current branch")
                logging.error(e.stderr)
        logging.info("pull: Execution terminated")
        return pull_success

    def destroy(self) -> None:
        """
        Destroys a local repo of oec.
        """
        logging.info("destroy: Execution started")
        # free the memory for gitPython and reset variables.
        if self.oec is not None:
            rmtree(self.root, onerror=self.__del_helper)\
                if not self.root == "" else None
            self.oec.__del__()
            self.__destroyed = True
            self.oec = None
            self.root = ""
            self.__remote = None
        logging.info("destroy: Execution terminated")

    def __del_helper(self, func, dir_path, exc):
        """
        rmtree throws Permission error at times, this helps to fix
        :param func: function used by rmtree to remove a dir
        :param dir_path: the path to remove
        :param exc:
        :return: None
        """
        chmod(dir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO |
              stat.S_IWRITE)  # 0777
        func(dir_path)

    def delete_branch(self, br_name="", remote=False) -> bool:
        """Deletes a branch from remote and local. if branch is empty string,
        will delete all the local branches but master. remote will be ignored
        :param br_name: branch to delete
        :param remote: delete from remote
        :return whether delete was success
        """
        logging.info("delete_branch: Execution started")
        del_success = False
        if self.__destroyed is not True:
            try:
                self.checkout()
                if br_name is not "master":
                    for indx in range(0, len(self.oec.branches)):
                        if br_name == "":
                            self.oec.delete_head(self.oec.branches[indx]) if \
                                self.oec.branches[indx].name != "master" \
                                else None

                        elif self.oec.branches[indx].name == br_name:
                            self.oec.delete_head(self.oec.branches[indx])
                            self.__remote.push(":" + br_name) if remote else \
                                None
                            del_success = True
                            break
            except git.exc.GitCommandError as e:
                logging.error(e.stderr)
        logging.info("delete_branch: Execution terminated")
        return del_success

    def submit(self, msg: str, branch_name: str,
               make_changes: Callable[[], bool]) -> str:
        """
        Submit a change to git as a branch
        :param msg: Commit message
        :param branch_name: branch name to create
        :param make_changes: func to create changes
        :return: the commit hash if changes were successful
        """
        # create branch branch_name and checkout branch_name
        logging.info("submit: Execution started")
        commit_hash = ""
        if self.__destroyed is not True:
            branch_result = self.branch(branch_name)
            # current branch self.oec.active_branch is no 'branch_name'
            # all further operations are on this branch till next checkout
            if branch_result is not "":
                # call make changes: if failed, delete branch and reset
                #  to master, return empty string.
                try:
                    func_result = make_changes()
                    if not func_result:
                        # switches to master
                        # deleted created branch from master
                        self.delete_branch(branch_name)
                    else:
                        # Else, commit, push, checkout master and return commit
                        # hash
                        # commit changes on this new branch
                        commit_hash = self.commit(msg)
                        # if commit was successful push this branch and
                        # checkout master.
                        if commit_hash != "":
                            self.push(branch_name)
                        else:
                            logging.error("Error occurred in commit.")
                        self.checkout()
                except Exception as e:
                    logging.error("Error occurred in Callable 'make_changes'")
                    logging.error(e)
                    self.delete_branch(branch_name)
                    commit_hash = ""
            else:
                logging.error("Error creating branch '"
                              + branch_name + "'")
        logging.info("submit: Execution terminated")
        return commit_hash

if __name__ == '__main__':
    # implement standalone app tester
    from os import getcwd
    appDir = getcwd() + "\\oec_clone"
    oec_repo = "https://github.com/OpenExoplanetCatalogue/open_exoplanet_" \
               "catalogue.git"

    oec = RepoManager(appDir, oec_repo)
    oec.destroy()
    print("Done")
