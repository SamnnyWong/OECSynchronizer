from tester_base import *
from repo_manager import *
from update_request import *
from syncutil import Helper, SrcPath


class RepoManagerTest(BaseTestCase):
    # Create git repository for testing
    def test_repo_manager(self):
        config_file = SrcPath.abs('config.yml')
        config = Helper.read_conf(config_file)
        url = ('https://%s:%s@github.com/teammask/hello-world.git' %
               (config['gh_username'], config['gh_api_token']))
        repo_path = os.path.join(self.SHARED_PATH, "test_repo")
        repo = RepoManager(repo_path, url)
        self.assertIsNotNone(repo)
        self.assertTrue(repo.root == repo_path)
        self.assertTrue(path.isdir(repo.root))
        self.assertTrue(repo.oec.description == RepoManager.REPO_BANNER)

        # Test commit: - Modify the readme file on master
        with open(os.path.join(repo_path, "README.md"), 'w') as readme_file:
            readme_file.write("Modified at: " + str(datetime.utcnow()))
        commit_hash = repo.commit("Test commit at: " + str(datetime.utcnow()))
        self.assertTrue(commit_hash != "")
        # forget last commit
        repo.oec.git.reset('--hard', 'HEAD~1')

        # Test branch and del_branch:-
        branch_result = repo.branch("ABCDE")
        self.assertTrue(branch_result == "ABCDE")
        self.assertTrue(repo.oec.active_branch.name == "ABCDE")
        self.assertTrue(repo.delete_branch("ABCDE", False))
        for branch in repo.oec.branches:
            self.assertTrue(branch.name != "ABCDE")
        branch_result = repo.branch("ABCDEG")

        # Test push
        self.assertTrue(repo.push(branch_result))
        found = False
        for branch in repo.oec.remote().refs:
            if branch.name == "origin/ABCDEG":
                found = True
                break
        self.assertTrue(found)
        # technically no branch was pushed if the commit reset was okay but
        # this line is here for good.
        repo.delete_branch("ABCDEG", True)

        # Test Pull. Any further testing is testing gitPython which is not
        # relevant
        self.assertTrue(repo.pull())

        # Test Destroy
        repo.destroy()
        self.assertIsNone(repo.oec)
        self.assertTrue(repo.root == "")
        self.assertFalse(path.isdir(repo_path))
