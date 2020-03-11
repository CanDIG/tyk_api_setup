import json
import re
import sys
import os
import logging

from json.decoder import JSONDecodeError
import requests

API_ID = ""


def setupCustomLogger(name=__name__):
    # Change here if you want another kind date format
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Change here if you want change the file name
    handler = logging.FileHandler(filename="log.txt")
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger


logger = setupCustomLogger()


def logInfo(msg):
    logger.info("{} -- {}".format(API_ID, msg))


def logWarning(msg):
    logger.warning("{} -- {}".format(API_ID, msg))


def getApiId(conf):
    return conf.get("CANDIG_API_ID", conf.get("AUTH_API_ID", ""))


def readGlobalConfigs():
    try:
        globalConfigs = readJsonFile("scripts/api_generator.conf.json")
    except FileNotFoundError:
        logWarning(
            "Please make sure you are executing this script from the root of tyk_api_setup."
        )
        logWarning("Aborting...")
        sys.exit()

    global policy_file_path_config
    global api_definition_output_path_config
    global tyk_secret
    global tyk_server_url

    policy_file_path_config = globalConfigs["policy_file_path_config"]
    api_definition_output_path_config = globalConfigs[
        "api_definition_output_path_config"]
    tyk_secret = globalConfigs["tyk_secret"]
    tyk_server_url = globalConfigs["tyk_server_url"]


def validateConf(conf):
    # Added as needed
    nonMandatoryFields = ["TYK_LISTEN_PATH"]

    for key, value in conf.items():
        if key not in nonMandatoryFields and not value:
            logger.warning("{} field should not be empty!".format(key))
            return False

    global API_ID
    API_ID = getApiId(conf)

    return True


def writeToJsonFile(outputJson, fileName):
    """
    Dumps "outputJson" into "filename" file
    """

    try:
        with open(fileName, "w") as file:
            json.dump(outputJson, file, indent=4)

        logInfo("New API successfully created.")

    except FileNotFoundError:
        logWarning(
            "Output directory for API definitions does not exist! Attempting to create..."
        )

        try:
            os.makedirs(api_definition_output_path_config)
            writeToJsonFile(outputJson, fileName)
        except OSError:
            logWarning(
                "You do not have sufficient permission to create specified directory!"
            )
            logWarning("Aborting...")
            sys.exit()


def isKey(key, value):
    return "${" + key + "}" in value


def replaceKey(key, value, item):
    return re.sub(r"\${" + key + r"}", value, item)


def readJsonFile(jsonFileName):
    """
    Read json data from "jsonFileName" file
    """
    with open(jsonFileName, "r") as json_file:
        data = json.load(json_file)

    return data


def replaceVariables(key, value, template):
    """
    Loops through "template" dictionary replacing values in format "${KEY}"
    to "value"
    """
    for template_key, template_value in template.items():
        if isinstance(template_value, dict):
            replaceVariables(key, value, template_value)

        elif isinstance(template_value, (int, bool)):
            continue

        elif isinstance(template_value, list):
            for index, item in enumerate(template_value):
                if isinstance(item, dict):
                    replaceVariables(key, value, item)
                else:
                    if isKey(key, item):
                        template_value[index] = replaceKey(key, value, item)

        elif isKey(key, template_value):
            template[template_key] = replaceKey(key, value, template_value)

        if isKey(key, template_key):
            template[value] = template[template_key]
            del template[template_key]

    return template


### policies set up


def writeToPoliciesJsonFile(outputJson):
    """
    Dumps "outputJson" into "filename" file
    """
    try:
        with open(policy_file_path_config, "w") as file:
            json.dump(outputJson, file, indent=4)

    except FileNotFoundError:
        logWarning(
            "Output directory for Policies definitions does not exist! Attempting to create..."
        )

        try:
            os.makedirs(policy_file_path_config.split("policies.json")[0])
            writeToPoliciesJsonFile(outputJson)
            logInfo("New policy successfully created.")
        except OSError:
            logWarning(
                "You do not have sufficient permission to create specified directory!"
            )
            logWarning("Aborting...")
            sys.exit()


def readPolicyFile(policy_file_path):
    try:
        with open(policy_file_path, "r") as policy_json_file:
            policy_data = json.load(policy_json_file)

        return policy_data

    except FileNotFoundError:
        return None


def writePolicy(api_config):
    new_api_policy = api_config["TYK_POLICY_ID"]
    try:
        new_api_id = api_config["CANDIG_API_ID"]
        new_api_name = api_config["CANDIG_API_NAME"]
    except KeyError:
        new_api_id = api_config["AUTH_API_ID"]
        new_api_name = api_config["AUTH_API_NAME"]

    new_api_policy_object = {
        "allowed_urls": [],
        "api_id": new_api_id,
        "api_name": new_api_name,
        "versions": ["Default"],
    }

    policy_data = readPolicyFile(policy_file_path_config)

    # case 1: policies.json exists

    if policy_data:
        logInfo("policies.json exists, updating...")
        if new_api_policy in policy_data:
            policy_data[new_api_policy]["access_rights"][
                new_api_id
            ] = new_api_policy_object
        else:
            misc_policy_config = {
                "active": True,
                "name": "CanDIG Policy",
                "rate": 100,
                "per": 1,
                "quota_max": 10000,
                "quota_renewal_rate": 3600,
                "tags": ["Startup Users"],
                "access_rights": {},
            }

            policy_data[new_api_policy] = misc_policy_config
            policy_data[new_api_policy]["access_rights"][
                new_api_id
            ] = new_api_policy_object

        writeToPoliciesJsonFile(policy_data)

    else:
        logInfo("policies.json does not exist, initializing...")
        policy_template = "templates/policies.json.tpl"
        policy_template_config = readJsonFile(policy_template)

        # For api_candig.conf.json

        if "CANDIG_API_ID" in api_config.items():
            for key, value in api_config.items():
                output_json = replaceVariables(
                    key, value, policy_template_config
                )

        # For api_auth.conf.json

        else:
            temp_api_auth_conf = {}
            temp_api_auth_conf["CANDIG_API_ID"] = api_config["AUTH_API_ID"]
            temp_api_auth_conf["CANDIG_API_NAME"] = api_config["AUTH_API_NAME"]
            temp_api_auth_conf["TYK_POLICY_ID"] = api_config["TYK_POLICY_ID"]

            for key, value in temp_api_auth_conf.items():
                output_json = replaceVariables(
                    key, value, policy_template_config
                )

        writeToPoliciesJsonFile(output_json)


### Keys setup


def requestKey(api_config):

    try:
        new_api_id = api_config["CANDIG_API_ID"]
        new_api_name = api_config["CANDIG_API_NAME"]
    except KeyError:
        new_api_id = api_config["AUTH_API_ID"]
        new_api_name = api_config["AUTH_API_NAME"]

    new_api_policy_object = {
        "allowed_urls": [],
        "api_id": new_api_id,
        "api_name": new_api_name,
        "versions": ["Default"],
    }

    key_template = "templates/key_request.json.tpl"
    key_template_config = readJsonFile(key_template)

    key_template_config["access_rights"] = {}
    key_template_config["access_rights"][new_api_id] = new_api_policy_object

    url = tyk_server_url + "/tyk/keys/create"
    headers = {
        "x-tyk-authorization": tyk_secret,
        "Content-Type": "application/json",
    }

    req = requests.post(
        url, headers=headers, data=json.dumps(key_template_config)
    )
    logInfo(req.text.strip())


### reload sevrver


def reload():

    headers = {"x-tyk-authorization": tyk_secret}
    r = requests.get(tyk_server_url + "/tyk/reload/group", headers=headers)
    logInfo(r.text.strip())


def main(confs):
    """
    confs ("str"): path to json file containing keys confs
    """
    readGlobalConfigs()

    conf_template_mapper = {
        "confs/api_auth.conf.json": "templates/api_auth.json.tpl",
        "confs/api_candig.conf.json": "templates/api_candig.json.tpl" 
    }

    try:
        auth_api = readJsonFile(confs)
    except JSONDecodeError:
        raise TypeError('The file "{}" is not a valid Json file'.format(confs))
    except FileNotFoundError:
        raise FileNotFoundError('Could not find the file "{}"'.format(confs))

    if not validateConf(auth_api):
        raise ValueError("Some values are missing on file {}".format(confs))

    if confs in conf_template_mapper:
        template_file_path = conf_template_mapper[confs]
    else:
        raise FileNotFoundError(
            'Could not locate template file for the conf.json file you specified. \
            Do not change the conf file name.'
        )

    try:
        template = readJsonFile(template_file_path)
    except JSONDecodeError:
        raise TypeError(
            'The file "{}" is not a valid Json file'.format(template_json)
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            'Could not find the file "{}"'.format(template_json)
        )

    for key, value in auth_api.items():
        template = replaceVariables(key, value, template)

    logInfo("Writing new API")

    global api_definition_output_path_config

    if api_definition_output_path_config[-1] != "/":
        api_definition_output_path_config += "/"

    file_name = api_definition_output_path_config + API_ID + ".json"

    writeToJsonFile(template, file_name)

    writePolicy(auth_api)

    requestKey(auth_api)

    reload()

    logInfo("API Setup completed...")

    return template


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Usage:")
        print("\tscripts/api_generator.py <confs/conf_file_name>")