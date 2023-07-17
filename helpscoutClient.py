import requests, os, datetime, json, sys

class helpscout_client:
    def __init__(self):
        self.client_id = os.environ["helpscout_client_id"]
        self.client_secret = os.environ["helpscout_client_secret"]
        self.token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=-1)
        self.base_url = "https://api.helpscout.net/v2/"
    
    def get_token(self):
        return requests.post(url= self.base_url + "oauth2/token", data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }).json()

    def check_token(self):
        if datetime.datetime.now() > self.token_expiry:
            token = self.get_token()
            self.access_token = token.get("access_token")
            self.token_expiry = datetime.datetime.now() + datetime.timedelta(seconds= token.get("expires_in"))
        pass

    def query(self, endpoint, parameters=""):
        self.check_token()
        number_of_attempts = 10
        for attempt in range(number_of_attempts):
            try:
                response = requests.get(url= self.base_url + endpoint + parameters, headers={
                    "Authorization": "Bearer " + self.access_token
                }).json()
            except:
                if attempt +1 == number_of_attempts:
                    return {"error": "Not Found"}
                continue
            else:
                return response
        else:
            print(f"We failed {attempt + 1} tries...")
            return

    def export_customers(self):
        page_info = {
            "totalPages": 1,
            "number": 0
        }
        
        while page_info["number"] < page_info["totalPages"]:
            response = self.query("customers", "?page=" + str(page_info["number"] + 1))
            page_info = response.get("page")
            print(page_info)

            filename = f"customers/page{page_info['number']}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
    
            with open(filename, "w") as file:
                json.dump(response.get("_embedded").get("customers"), file)

        return
    
    def export_agents(self):
        page_info = {
            "totalPages": 1,
            "number": 0
        }

        while page_info["number"] < page_info["totalPages"]:
            response = self.query("users")
            page_info = response.get("page")
            print(page_info)

            filename = f"agents/page{page_info['number']}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
    
            with open(filename, "w") as file:
                json.dump(response.get("_embedded").get("users"), file)

        return

    def get_attachment(self, conversationId, attachmentId):
        print(f"Querying conversations/{conversationId}/attachments/{attachmentId}/data")
        response = self.query(f'conversations/{conversationId}/attachments/{attachmentId}/data')
        return response

    def export_tickets(self):
        page_info = {
            "totalPages": 1,
            "number": 0,
        }
        
        while page_info["number"] < page_info["totalPages"]:
            response = self.query("conversations", "?page=" + str(page_info["number"] + 1) + "&status=all" + "&embed=threads")
            page_info = response.get("page")
            print(page_info)

            filename = f"tickets/page{page_info['number']}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
    
            with open(filename, "w") as file:
                json.dump(response.get("_embedded").get("conversations"), file)

        return

if __name__ == "__main__":
    hsClient = helpscout_client()
    print(json.dumps(hsClient.get_tickets(), indent=2))
