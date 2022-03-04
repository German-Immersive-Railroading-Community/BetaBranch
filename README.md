# The Betabranch System
The System which let's the Betabranches work.

## .env Files
There are two env files. One for the main server and one for the test.  
Main:
```
cert_path=<path to .pem certificate>
priv_path=<path to privatekey.pem>
full_path=<path to fullchain.pem>
secret=<the secret from the webhook>
json_file=<path to the folder of the beta.json>
testURL=<test.server.domain:port>
log_level=<DEBUG, INFO, ...>
logDir=<directory in which the logs should be saved>
gh-actions=<list of the actions of PRs which should be processed (opened, closed, ...)>
```

Test:
```
server_files=<path to folder where the folders for the testing servers are copied from>
server_folder=<path to folder where the testing servers are created>
min_port=<lowest port to use>
max_port=<highest port to use>
log_level=<DEBUG, INFO, ...>
logDir=<directory in which the logs should be saved>
fallback_server_files=<the server files that should be used if the files for mc_version do not exist, must be located in server_files-folder>
```
