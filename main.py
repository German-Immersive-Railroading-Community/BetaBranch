from github import Github
from vars import *
import os

def download_link(sha):
    return f"https://codeload.github.com/{repo_name}/zip/{sha}"
# using an access token
g = Github(access_token)
repo = g.get_repo(repo_name)

# go through all pull requests
for pull in repo.get_pulls(state='closed', sort='created', direction = "desc", base='master'):
    # get newest commit out of pull request
    coms = pull.get_commits()
    id = pull.number
    com = coms[coms.totalCount-1]
    # download and compile jar file
    os.system(f"wget -qO prs/{id}.zip {download_link(com.sha)}")
    os.system(f"unzip prs/{id} -d prs/")
    folder = f"{repo.name}-{com.sha}"
    os.system(f"chmod +x prs/{folder}/gradlew")
    os.system(f"cd prs/{folder}/;./gradlew build")
    os.system(f"cp prs/{folder}/build/libs/GIRSignals.jar jars/GIRSignals{id}.jar")
    os.system("rm -R prs/*")
