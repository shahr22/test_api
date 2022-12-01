import json
import parsing
import msal
import requests
import base64

# Parameters
# with open('./params.json') as file:
#     f=file.read()

# config = json.loads(f)
import boto3
from botocore.exceptions import ClientError

def get_secret():

    secret_name = "PowerAutoTest"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']

    return json.loads(secret)

def handler(event, context):
    # Initial event parse
    print('Parsing events...')
    data = event['body']
    parsed = json.loads(data)

    # Get secrets
    config = get_secret()
    api_cred = config['graph_key']

    # Parsing Inputs
    check_for = ["pairing","screening"]
    body_templates = {
        "default": "body1",
        "pairing": "body2",
        "screening": "body3"
    }
    # Calender parsing
    send_time = parsing.time_conversion(parsed, 1)
    check_result = parsing.subject_check(parsed, check_for)
    body = parsing.body_pick(check_result, check_for, body_templates)
    recipients = parsing.recipients_formated(parsed)
    email = json.dumps(parsing.build_mail(check_result["subject"], body, recipients,send_time))
    print(email)
    print('Email built. Authenticating to Graph API...')

    # Client Object
    # Client Object
    app = msal.ConfidentialClientApplication(
        config["client_id_1"], authority=config["authority1"],
        client_credential=api_cred)

    result = None

    scope = [ "https://graph.microsoft.com/.default" ]
    email_endpoint = "https://graph.microsoft.com/v1.0/users/"+data['code']+"/sendmail"

    if not result:
        result = app.acquire_token_for_client(scopes=scope)

    # Calling graph using the access token
    if "access_token" in result:
        print('Token recieved. Scheduling email...')
        graph_data = requests.post( 
            email_endpoint,
            headers={'Authorization': 'Bearer ' + result['access_token']},
            json=parsing.build_mail(check_result["subject"], body, recipients,send_time),
            )
        if graph_data.ok:
            return {
                'statusCode': 200,
                'body': "Success. Email scheduled"
            }
        else:
            print(graph_data.json())
        
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  
        if 65001 in result.get("error_codes", []):  
            # AAD requires user consent for U/P flow
            print("Visit this to consent:", app.get_authorization_request_url(scope))