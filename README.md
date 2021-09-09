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
```

Test:
```
server_files=<path to folder where the files for the testing servers are copied from>
server_folder=<path to folder where the testing servers are created>
min_port=<lowest port to use>
max_port=<highest port to use>
```
