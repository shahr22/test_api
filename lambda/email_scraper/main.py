import json
import logging
import requests
import msal
import csv
import time
import base64
from io import StringIO
import requests
import base64
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
    start = time.time()
    # Initial event parse
    print('Parsing events...')
    # data = event['body']
    # parsed = json.loads(data)
    target_email = event['email']

    # Set logging level to info
    logging.getLogger().setLevel(logging.INFO)

    # Get secrets
    config = get_secret()

    # Client Object
    logging.info("Authenticating into Graph API...") 
    app = msal.ConfidentialClientApplication(
        config["client_id"], authority=config["authority"],
        client_credential=config['graph_key'])

    result = None

    scope = [ "https://graph.microsoft.com/.default" ]
    users_ep = "https://graph.microsoft.com/v1.0/users"

    if not result:
        result = app.acquire_token_for_client(scopes=scope)

    # Calling graph using the access token
    if "access_token" in result:
        logging.info("Searching directory for user id") 
        user_search = requests.get(  
            users_ep+f"?$filter=mail eq '{target_email}'",
            headers={'Authorization': 'Bearer ' + result['access_token']},).json()
        user_id = user_search['value'][0]['id']

        logging.info("Getting mail folder IDs") 
        graph_data = requests.get(  
            users_ep+f"/{user_id}/mailFolders",
            headers={'Authorization': 'Bearer ' + result['access_token']},).json()

        # We will scrape inbox and sent folders
        values = graph_data['value']
        for value in values:
            # print(value['displayName'])
            if value['displayName']=='Inbox':
                inbox_id = value['id']
                inbox_count = value['totalItemCount']
            if value['displayName']=="Sent Items":
                sent_id = value['id']
                sent_count = value['totalItemCount']

        logging.info(f"Preliminary logic elapsed time: {time.time()-start}s\nNow sending batch calls...")
        
        all_esets = []

        batch_start_time = time.time()

        # gets unique emails via set function

        def get_email_set(inbox_data):
            email_set = set()
            for email in inbox_data['value']:
                all = email['toRecipients'] + email['ccRecipients'] + email['bccRecipients']
                all.append(email['from'])
                all = [data['emailAddress'] for data in all]
                all = map(lambda x: json.dumps(x, sort_keys=True), all) # we serialize dictionaries to use sets over them
                all = set(list(all))
                email_set = email_set.union(all)
            return email_set

        # formatting for batch requests. 

        def batch_formater(batch):
            return [{"id": batch.index(url)+1,"method": "GET","url": url} for url in batch]
        
        # We take the total inbox size, cut it into groups of 10 or less (10 is max returnable emails per call), and create url calls/queries for each group of 10
        # Batch requests can handle 20 requests in one call. We create list of lists with 20 urls each, and then format appropriately 

        def batch_requests(mail_folder_id, mail_count):
            all_url = [f"/users/{user_id}/mailFolders/{mail_folder_id}/messages?%24select=toRecipients%2cccRecipients%2cbccRecipients%2cfrom&%24top=10&%24skip={skip}" for skip in range(0,mail_count,10)]
            batch_urls = [all_url[i:i+20] for i in range(0, len(all_url), 20)]
            all_batch_requests = list(map(batch_formater, batch_urls))
            return all_batch_requests

        # graph batch call combines previous functions to get email data and store into a set

        def graph_batch_call(mail_folder_id, mail_count):
            for batch_request in batch_requests(mail_folder_id, mail_count):
                bstart = time.time()
                json_batch_req = json.dumps(
                    {
                        "requests": batch_request
                    }
                )
                response = requests.post(  
                "https://graph.microsoft.com/v1.0/$batch",
                headers={
                    'Authorization': 'Bearer ' + result['access_token'],
                    'Content-Type': 'application/json'
                },
                data=json_batch_req
                ).json()
                print(f"batch call time elapsed: {time.time()-bstart}s")
                for r in response['responses']:
                    all_esets.append(get_email_set(r['body']))


        graph_batch_call(inbox_id, inbox_count) 
        graph_batch_call(sent_id,sent_count)

        batch_end_time = time.time()

        logging.info("All batch calls --- %s seconds ---" % (batch_end_time - batch_start_time))

        # unpack set, deserialize, and prepare for csv writer

        t0 = time.time()
        total_email_set = set.union(*all_esets)
        emails = list(map(lambda x: json.loads(x), total_email_set))
        names = [data['name'] for data in emails]
        address = [data['address'] for data in emails]
        t1 = time.time()

        logging.info(f"Parsing logic time elapsed: {t1-t0}s. Now Creating CSV...")

        # We use email to send csv file. String IO and base64 encode prepares csv for sending via graph api
        
        str_io=StringIO()
        writer = csv.writer(str_io)
        for (n, a) in zip(names, address):
            if ',' in n:
                name = n.replace('"','')
                name = name.split(', ')
                name.reverse()
                name = ' '.join(name)
            else:
                name = n
            writer.writerow([name, a])
        attachment = base64.b64encode(str_io.getvalue().encode())

        t2 = time.time()

        logging.info(f"CSV creation logic time elapsed: {t2-t1}s. \nNow Sending Email...")

        # build and format functions for sending email. functions from interview reminder

        def build_mail(subject: str, body: str, recipients: str, **kwargs):
            request_body = {
                        "Message": {
                            "subject": subject,
                            "body": {
                            "contentType": "Text",
                            "content": body
                            },
                            "toRecipients": recipients,
                            }
                        }
            if "send_time" in kwargs:
                request_body["Message"]["singleValueExtendedProperties"] = [
                    {
                        "id":"SystemTime 0x3FEF",
                        "value": kwargs["send_time"]
                    }
                    ]
            if "attachment" in kwargs:
                print("Attaching...")
                request_body["Message"]["attachments"] = [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": kwargs["attachment"]["name"],
                        "contentBytes": kwargs["attachment"]["bytes"]
                    }
                    ]


            return request_body

        # Input string of emails with semicolon seperator. If one, use semicolon at end

        def recipients_formated(parsed):
            atendees = parsed.split(";")
            recipients_data = []
            for email in atendees[:-1]:
                data = {
                        'emailAddress': {
                            'address': email
                        }
                    }
                recipients_data.append(data)
            return recipients_data 

        email_endpoint = f"{users_ep}/{user_id}/sendmail"
        send_email = requests.post( 
            email_endpoint,
            headers={'Authorization': 'Bearer ' + result['access_token']},
            json=build_mail("All emails csv", 
                body="Attached are the requested emails.", 
                recipients=recipients_formated(target_email+";"),  
                attachment={"name": "emails.csv","bytes": attachment.decode("utf-8")}),
            )
        if send_email.ok:
            logging.info("Sent email succesfully.")
        else:
            print(send_email.json())

        logging.info(f"Done. Total time elapsed: {time.time()-start}s") 
            
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  
        if 65001 in result.get("error_codes", []):  
            print("Visit this to consent:", app.get_authorization_request_url(scope))