from ..base.m4c_base import M4CBase
from jinja2 import Template
import markdown
import requests
import json
import os
import time

token = os.environ['FRONT_API_TOKEN']

class FrontAPIWrapper:

    def channels(self):        
        return self.get('channels')

    def create_message(self, channel_id, data):
        route = f"channels/{channel_id}/messages"
        return self.post(route, data)

    def get(self, route):
        url = "https://api2.frontapp.com/" + route
        response = requests.request("GET", url, headers = {"Authorization":"Bearer " + token})
        return response.json()

    def post(self, route, payload):
        url = "https://api2.frontapp.com/" + route
        headers = {
            'content-type': 'application/json',
            "Authorization": "Bearer " + token
        }    
        response = requests.request("POST", url, data = json.dumps(payload), headers = headers)
        result = response.json()
        return result


class AutoNotification:
    def __init__(self):
        self.front = FrontAPIWrapper()
        self.base = M4CBase()

    def triggers(self):
        return []

    def action(self, trigger):
        pass

    def run(self):
        triggers = self.triggers()
        for trigger in triggers:            
            self.action(trigger)        
            time.sleep(1) # respect the time limit

    def send_email(self, address, subject, body):
        
        payload = {
            "sender_name": "Make4Covid",
            "to": [address],
            "subject": subject,
            "body": body        
        }
        return self.front.create_message('cha_3yb0x', payload)


    def update_airtable_record(self, record, result, link_column_name):

        message_id = result['id']
        record_id = record['id']
        email = record['fields']['Confirmation Email']

        perm_link = f'https://app.frontapp.com/open/{message_id}'

        import datetime
        sent_on = datetime.datetime.fromtimestamp(result['created_at'])    
        log = f'''\
From: Make4Covid
To: {email}
Sent: {sent_on}
Subject: {result['subject']}

{result['body']}
''' 

        message_log = record['fields'].get('Message Log','')
        new_message_log = message_log + log + '\n-------------------\n'
        
        update_data = {
            link_column_name: perm_link,
            'Message Log': new_message_log
        }

        self.base.maker_supply_requests.update(record_id, update_data)


template_tracking_info = Template('''\
Dear {{full_name}},

Your Material Request has been shipped, and your Fedex Tracking number is {{tracking_info}}.

Your requests:

{{material}} {{material_2}}.

Your shipping address:

{{street_address}}
{{city}}
{{state}} {{zipcode}}

Thank you!

Make4Covid

''')

template_order_processed_message = Template('''\
Dear {{full_name}},

Your Material Request has been received and sent to the vendor for processing.

Your requests:

{{material}} {{material_2}}.

Your shipping address:

{{street_address}}
{{city}}
{{state}} {{zipcode}}

Thank you!

Make4Covid
''')
    

def generate_message(record, template):

    tracking_info = record['fields'].get('Tracking info', '')
    email = record['fields']['Confirmation Email']
    full_name = record['fields']['Full Name'][0]
    material = record['fields']['Material']
    material_2 = record['fields']['Material 2']
    street_address = record['fields'].get('Street Address', [''])[0]
    city = record['fields'].get('City', [''])[0]
    state = record['fields'].get('State', [''])[0]
    zipcode = record['fields'].get('Zip', [''])[0]

    text = template.render(**locals())
    html = markdown.markdown(text)
    return html


class OrderProcessedNotification(AutoNotification):

    def triggers(self):        
        return self.base.maker_supply_requests.get_all(view='[Auto] Notify Order Processed')                

    def action(self, trigger):

        # def action()
        record = trigger
        text = generate_message(record, template_order_processed_message)
        
        address = record['fields']['Confirmation Email']
        result = self.send_email(address, 'Your supply request has been processed', text)

        self.update_airtable_record(record, result, '[Auto] Notify Order Processed')

class TrackingInfoNotification(AutoNotification):

    def triggers(self):        
        return self.base.maker_supply_requests.get_all(view='[Auto] Send Tracking Info')

    def action(self, trigger):

        record = trigger
    
        text = generate_message(record, template_tracking_info)
        subject = 'Your supply request has been shipped. Tracking #: ' + record['fields']['Tracking info']
        
        address = record['fields']['Confirmation Email']
        result = self.send_email(address, subject, text)

        self.update_airtable_record(record, result, '[Auto] Send Tracking Info')