import requests, os, json

class freshdesk_client:
    def __init__(self):
        self.api_key = os.environ["freshdesk_api_key"]
        self.base_url = "https://nexar.freshdesk.com/api/v2/"
        self.endpoints = {
            "all_ticket_fields": "ticket_fields/"
        }
    
    def get_request(self, endpoint):
        return requests.get(url= self.base_url + endpoint, auth=(self.api_key, "")).json()

    def get_all_ticket_fields(self):
        fields = self.get_request(self.endpoints["all_ticket_fields"])
        print(json.dumps(fields, indent=2))

fd_client = freshdesk_client()
fd_client.get_all_ticket_fields()