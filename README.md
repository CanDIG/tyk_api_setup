## Usage


### Step 1

Go to ```/scripts/api_generator.conf.json``` and update `tyk_secret` and `tyk_server_url`. This is very important as it enables the script to call Tyk REST API endpoints to create keys and do hot reload.

Change `policy_file_path_config` and `api_definition_output_path_config` if needed. They are default to the Tyk default paths. You want to make sure that you run the script as someone who has W access to these directories.

You should only need to do it once.

### Step 2

If you are setting up Authentication APIs, please use ```confs/api_auth.conf.json```.

If you are setting up candig-server, please use ```api_candig.conf.json```.

You will need to fill out required fields in the corresponding `.conf` files.

To generate the API, you should go to the root of ```tyk_api_setup``` and execute below command where:
- ```path/to/conf/file``` -> Path to configuration file under ```confs/``` 

```
$ python scripts/api_generator.py path/to/conf/file
```

This command generates a file with the same name as ```API_iD``` on the ```confs``` file.


## Requirements
- Python 3+
- requests (You may want to install this in a virtualenv)


## Write your conf file

- `TYK_LISTEN_PATH` should not have any slashes.


## Limitations

- The script does not support the addition of multiple OIDC Providers yet, in order to add peer keycloaks for federation to work, you will need to manually edit the output API definition files. When you are done editing the API definitions files, you should do a hot reload, or restart Tyk. Instructions to add peer keycloaks are in `ManualSetup.md`.

- The script does not support the custom configs that vary from environment to environment: some places have their SSL certificates somewhere else, and nothing needs to be set up here. If you want to set up mutual TLS, you should add `upsteam_certificates` as the key to your API definition file, and value being `{"$TYK_SERVER_ADDRESS": "<cert-id>"}.`.
