import json
import datetime as dt


# parse time data and get send time
def time_conversion(parsed, day_delta: int):
    start = parsed["body"]["start"].split("T")
    day = dt.datetime.strptime(start[0], "%Y-%m-%d")
    # startt = parsed["body"]["start"]
    # startt = dt.datetime.strptime(startt, "%Y-%m-%dT%H:%M:%S.0000000")
    remind_day = day - dt.timedelta(days=day_delta)
    remind_day = remind_day.strftime("%Y-%m-%dT"+start[1])
    return remind_day


# parse subject data, look for specific meeting types
def subject_check(parsed, check_for: list):
    subject_line = parsed["body"]["subject"]
    data = {
        "subject" : subject_line
    }
    for check in check_for:
        data[check] = False
        if check in subject_line.lower():
            data[check] = True
    return data

# pick which body to use
def body_pick(check_result: dict, check_for: list, body_templates: dict):
    body = body_templates["default"]
    for check in check_for:
        if check_result[check] == True:
            body = body_templates[check]
            return body
    return body

# format recipient emails
def recipients_formated(parsed):
    atendees = parsed["body"]["requiredAttendees"] #+ parsed["body"]["optionalAttendees"]
    atendees = atendees.split(";")
    recipients_data = []
    for email in atendees[:-1]:
        data = {
                'emailAddress': {
                    'address': email
                }
            }
        recipients_data.append(data)
    return recipients_data 

# send_mail structure
def build_mail(subject: str, body: str, recipients: str, time: str):
    request_body = {
                    "Message": {
                        "subject": subject,
                        "body": {
                        "contentType": "Text",
                        "content": body
                        },
                        "toRecipients": recipients,
                        "singleValueExtendedProperties": 
                        [
                        {
                            "id":"SystemTime 0x3FEF",
                            "value": time
                        }
                        ]
                    }
                    }
    return request_body