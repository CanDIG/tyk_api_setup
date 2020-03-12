# Overview

### The following instruction is adapted from https://github.com/CanDIG/candig_compose/blob/a7448f3c5b46eb8fc45201a87b5ac0b51872b6ab/README.md

## Shut down your tyk-dashboard
This part isn't strictly necessary, but the tyk-dashboard will be of no use.

## Update your tyk.conf
The following section assumes you are migrating from the config to be used with Tyk-dashboard

The tyk.conf is different for file-based API setup, vs the dashboard API setup.

You could also check things listed here https://tyk.io/docs/try-out-tyk/tutorials/important-prerequisites/, but the changes listed here should be everything you need to make.


In particular, if your current tyk.conf is prepared to use with the Tyk-dashboard, you should remove both fields here.

```
"use_db_app_configs": true,
  "db_app_conf_options": {
        "connection_string": "",
        "node_is_segmented": false,
        "tags": []
  },
```

You should also make sure you are explicitly specifying the policies file location

```
"policies": {
    "policy_source": "file",
    "policy_record_name": "policies/policies.json"
  },
```

You should also make sure you are explicitly specifying the apps (where API definitions go into) location

```
"app_path": "/opt/tyk-gateway/apps",
```

## Add APIs

Prepare the API definition

Use https://raw.githubusercontent.com/CanDIG/candig_compose/a7448f3c5b46eb8fc45201a87b5ac0b51872b6ab/template/config.tpl/tyk/confs/api_auth.json.tpl as a template for authentication endpoint.

Use https://github.com/CanDIG/candig_compose/blob/a7448f3c5b46eb8fc45201a87b5ac0b51872b6ab/template/config.tpl/tyk/confs/api_candig.json.tpl as a template for candig-server endpoints.

For api_id, name, slug, use something that helps you organize. The config_data would be the same as before.

Remember, `api_id, name, slug` should be unique among the APIs you add.

Save it as api_${name_of_your_choice}.json under /opt/tyk-gateway/apps


## Add Peer Keycloak for Federation

Add it under `providers`, an example would be 

```
{
	"openidoptions": {
		"providers": [
			{
				"issuer": "http://candigauth.siteA.ca/auth/realms/candig",
				"clientids": {
					"client1base64": "policy1"
				}
			},
			{
				"issuer": "http://candigauth.siteB.ca/auth/realms/CanDIG",
				"clientids": {
					"client2base64": "policy1"
				}
			}
		],
		"segregateby_client": false
	}
}
```

As you can see, it's just one more entry under providers, which is a list.



## Update the policy

Use https://github.com/CanDIG/candig_compose/blob/a7448f3c5b46eb8fc45201a87b5ac0b51872b6ab/template/config.tpl/tyk/confs/policies.json.tpl as a template.

The important part here is the access_right


```
"access_rights": {
            "${CANDIG_API_ID}": {
                "allowed_urls": [],
                "api_id": "${CANDIG_API_ID}",
                "api_name": "${CANDIG_API_NAME}",
                "versions": [
                    "Default"
                ]
            }
        }
```

All policies should be written within the same policies.json.

Request a new key
Use https://github.com/CanDIG/candig_compose/blob/a7448f3c5b46eb8fc45201a87b5ac0b51872b6ab/template/config.tpl/tyk/confs/key_request.json.tpl as a template and add your new API.

Now, you will need to make a curl request. You will need the secret from tyk.conf to make the request.

```
$ curl ${TYK_HOST}:${TYK_PORT}/tyk/keys/create -H "x-tyk-authorization: ${TYK_SECRET}" -s -H "Content-Type: application/json" -X POST -d '{
	"allowance": 1000,
	"rate": 1000,
	"per": 1,
	"expires": -1,
	"quota_max": -1,
	"org_id": "",
	"quota_renews": 1449051461,
	"quota_remaining": -1,
	"quota_renewal_rate": 60,
    "access_rights": {
        "auth_api_id": {
            "api_id": "auth_api_id",
            "api_name": "Authentication",
            "versions": ["Default"]
        },
    },
    "meta_data": {}
}
'
```
## Reload your tyk-gateway
A hot reload is 
```
curl -H "x-tyk-authorization: ${TYK_SECRET}" -s ${TYK_HOST}:${TYK_PORT}/tyk/reload/group
```
Or you can reload from command line.







