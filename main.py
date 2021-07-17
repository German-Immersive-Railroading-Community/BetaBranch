from github import Github
from vars import *
import os

def download_link(sha):
    return f"https://codeload.github.com/{repo_name}/zip/{sha}"
# using an access token
g = Github(access_token)
repo = g.get_repo(repo_name)
for pull in repo.get_pulls(state='opem', sort='created', base='master'):
    coms = pull.get_commits()
    com = coms[coms.totalCount-1]
    os.system(f"wget -qO prs/{pull.number}.zip {download_link(com.sha)}")
