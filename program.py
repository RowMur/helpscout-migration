from helpscoutClient import helpscout_client
import csv, base64, os, json, sys

def json_export(filename, data):
    with open(filename + ".json", "w") as file:
        json.dump(data, file)

def format_customers():
    page = 1
    with open("helpscout_contacts.csv", "w") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(["contact id", "contact name", "contact email", "mobile", "phone", "is active"])
    while True:
        filename = f"customers/page{page}.json"

        if not os.path.isfile(filename):
            break

        with open(filename, "r") as json_file:
            with open("helpscout_contacts.csv", "a", encoding="utf-8", newline="") as csv_file:
                writer = csv.writer(csv_file, delimiter=",")
                customers = json.load(json_file)
                total_no_email_customers = 0
                for customer in customers:
                    row = [customer.get("id")]
                    
                    if not customer.get("_embedded").get("emails"):
                        total_no_email_customers += 1
                        continue

                    if customer.get("firstName") or customer.get("lastName"):
                        row.append(str.strip(customer.get("firstName") + " " + customer.get("lastName")))
                    else:
                        email = customer.get("_embedded").get("emails")[0].get("value")
                        username = email[:email.index("@")]
                        row.append(username)
                    
                    row.append(customer.get("_embedded").get("emails")[0].get("value"))
                    writer.writerow(row)
                
        print(f"Completed page {page}")
        page += 1
    
    print(f"Total no email customers: {total_no_email_customers}")

def format_agents():
    page = 1
    with open("helpscout_agents.csv", "w") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(["agent id", "agent email", "scope", "agent name", "mobile", "phone"])

    while True:
        filename = f"agents/page{page}.json"

        if not os.path.isfile(filename):
            break

        with open(filename, "r") as json_file:
            with open("helpscout_agents.csv", "a", encoding="utf-8", newline="") as csv_file:
                writer = csv.writer(csv_file, delimiter=",")
                agents = json.load(json_file)

                for agent in agents:
                    row = [agent.get("id"), agent.get("email"), agent.get("role"), str.strip(agent.get("firstName") + " " + agent.get("lastName"))]
                    writer.writerow(row)
        
        print(f"Completed page {page}")
        page += 1

def format_tickets(isUpdated):
    page = 1
    
    tickets_file = open("helpscout_tickets.csv", "w", newline="", encoding="utf-8")
    tickets_writer = csv.writer(tickets_file, delimiter=",")
    tickets_writer.writerow(["ticket id", "status", "priority", "created_at", "updated_at", "subject",  "description", "ticket-type", "ticket source", "contact id", "contact email", "agent id", "agent email", "group id", "company id", "tags", "Inbox"])
    
    conversations1_file = open("helpscout_conversations_1.csv", "w", newline="", encoding="utf-8")
    conversations1_writer = csv.writer(conversations1_file, delimiter=",")
    conversations1_writer.writerow(["notes id", "ticket id", "body", "is private note", "user id(Contact/Agent)", "created_at", "updated_at"])

    conversations2_file = open("helpscout_conversations_2.csv", "w", newline="", encoding="utf-8")
    conversations2_writer = csv.writer(conversations2_file, delimiter=",")
    conversations2_writer.writerow(["notes id", "ticket id", "body", "is private note", "user id(Contact/Agent)", "created_at", "updated_at"])
    
    while True:
        if isUpdated:
            filename = f"updatedTickets/page{page}.json"
        else:
            filename = f"tickets/page{page}.json"

        if not os.path.isfile(filename):
            break
        
        with open(filename, "r") as json_file:
                
            tickets = json.load(json_file)
            for ticket in tickets:

                # Ignore jobs inbox
                if ticket.get("mailboxId") == 99173:
                    continue
                row = [ticket.get("id"), ticket.get("status"), "low", ticket.get("createdAt"), ticket.get("userUpdatedAt"), f"\"{ticket.get('subject')}\"", "<div>" + ticket.get("preview") + "</div>", ticket.get("type"), ticket.get("source").get("type")]
                if ticket.get("createdBy").get("email") != "":
                    row.append(ticket.get("createdBy").get("id"))
                    row.append(ticket.get("createdBy").get("email"))
                else:
                    continue
                if ticket.get("assignee") is not None:
                    row.append(ticket.get("assignee").get("id"))
                    row.append(ticket.get("assignee").get("email"))
                else:
                    row.append("")
                    row.append("")
                row.append("")
                row.append("")
                if ticket.get("tags") is not None:
                    tags = ""
                    for index, tag in enumerate(ticket.get("tags")):
                        if index != 0:
                            tags += ";"
                        tags += tag.get("tag")                        
                    row.append(tags)
                else:
                    row.append("")
                match ticket.get("mailboxId"):
                    case 72412:
                        row.append("Contact")
                    case 73718:
                        row.append("API")
                    case 73846:
                        row.append("Support")
                    case 162560:
                        row.append("Billing")
                
                tickets_writer.writerow(row)

                if ticket.get("_embedded").get("threads"):
                    for thread in ticket.get("_embedded").get("threads"):
                        if thread.get("type") == "customer" and thread.get("customer") is not None:
                            user_id = thread.get("customer").get("id")
                        elif thread.get("assignedTo") is not None:
                            user_id = thread.get("assignedTo").get("id")
                        else:
                            user_id = ""
                        if thread.get("type") == "note":
                            is_private_note = True
                        else:
                            is_private_note = False
                        if thread.get("body"):
                            body = thread.get("body").replace("\n", "<br>")
                        else:
                            body = ""
                        if page % 2 == 1:
                            conversations1_writer.writerow([thread.get("id"), ticket.get("id"), body, is_private_note, user_id, ticket.get("createdAt"), ticket.get("createdAt")])
                        else:
                            conversations2_writer.writerow([thread.get("id"), ticket.get("id"), body, is_private_note, user_id, ticket.get("createdAt"), ticket.get("createdAt")])

        if page % 50 == 0:
            print(f"Completed page {page}")
        page += 1        

    tickets_file.close()
    conversations1_file.close()

def get_attachments(isUpdated):
    client = helpscout_client()
    page = 1
    attachment_count = 0
    while True:
        if not isUpdated:
            json_filename = f"tickets/page{page}.json"
        else:
            json_filename = f"updatedTickets/page{page}.json"

        if not os.path.isfile(json_filename):
            break

        with open(json_filename, "r") as json_file:
            tickets = json.load(json_file)
            for ticket in tickets:
                if (ticket.get("status") != "active"  and ticket.get("status") != "open") or ticket.get("mailboxId") != 72412:
                    continue
                for thread in ticket.get("_embedded").get("threads"):
                    if thread.get("_embedded").get("attachments"):
                        # print(f"Writing to folder: attachments/{thread.get('id')}")
                        print()
                    else:
                        continue
                    print(len(thread.get("_embedded").get("attachments")))
                    print(ticket.get("subject"))
                    print(thread.get("id"))
                    for attachment in thread.get("_embedded").get("attachments"):
                        print(attachment.get("filename"))
                        attachment_count += 1
                        # response = client.get_attachment(conversationId=ticket.get("id"), attachmentId=attachment.get("id"))
                        # if response.get("error"):
                        #     continue
                        # decoded_data = base64.b64decode(response.get("data"))
                        # filename = f"attachments/{thread.get('id')}/" + attachment.get("filename").replace("?", "").replace(":", "")
                        # os.makedirs(os.path.dirname(filename), exist_ok=True)
                        
                        # if (decoded_data):
                        #     with open(filename, "wb") as file:
                        #         file.write(decoded_data)

        # print(f"Completed page {page}")
        page += 1
    
    print(attachment_count)




    # conversations = open("helpscout_conversations.csv", "r", encoding="utf-8").readlines()
    # for conversation in conversations:
    #     print(conversation)

if __name__ == "__main__":
    client = helpscout_client()
    # client.export_customers()
    # client.export_agents()
    # client.export_tickets()
    # client.export_updated_tickets("2023-07-15T12:00:00Z")

    # format_customers()
    # format_agents()
    format_tickets(False)

    # get_attachments(True)
