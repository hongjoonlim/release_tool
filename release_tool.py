import argparse
import json
import os
import re
from git import Repo

class VersionUpdater:
    def __init__(self, config_path):
        self.config_path = config_path
        self.version_keys = []
        self.repo_paths = []
        self.files = []
        self.old_version = ""
        self.new_version = ""
        self.load_config()

    def load_config(self):
        with open(self.config_path) as f:
            config = json.load(f)

        self.version_keys = config["version_info"]
        self.repo_paths = config["repositories"]
        self.files = config["files"]
        self.old_version = config["old_version"]
        self.new_version = config["new_version"]

    def update_version(self):
        for repo_path in self.repo_paths:
            if not os.path.exists(repo_path):
                print(f"Error: {repo_path} does not exist")
                continue

            repo = Repo(repo_path)
            if repo.active_branch.name != 'development':
                print(f"Error: {repo_path} is not on development branch")
                continue

            release_branch_name = f"release/{self.new_version}"
            if release_branch_name in repo.heads:
                print(f"{release_branch_name} already exists")
                continue

            release_branch = repo.create_head(release_branch_name)
            repo.head.reference = release_branch

            for file in self.files:
                file_path = os.path.join(repo_path, file["path"])
                if not os.path.exists(file_path):
                    print(f"Error: {file_path} does not exist")
                    continue

                with open(file_path, "r") as f:
                    contents = f.read()

                for version_key in self.version_keys:
                    pattern = re.compile(f"({version_key})(\\s*=\\s*)('{self.old_version}')")
                    match = pattern.search(contents)
                    if match:
                        contents = contents[:match.start(3)] + f"{self.new_version}" + contents[match.end(3):]

                with open(file_path, "w") as f:
                    f.write(contents)

            self.git_commit(repo)
            self.git_push(repo)

    def git_commit(self, repo):
        repo.git.add(update=True)
        repo.index.commit("Version number increased")

    def git_push(self, repo):
        origin = repo.remote(name='origin')
        origin.push(refspec=f"refs/heads/{repo.active_branch.name}")
        origin.push(refspec=f"refs/heads/release/{self.new_version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="path to the config.json file")
    args = parser.parse_args()

    if not args.config:
        print("Error: config file path is required")
        exit(1)

    updater = VersionUpdater(args.config)
    updater.update_version()
