from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

import requests
import os
import json

class ActionCheckSufficientFunds(Action):
    def name(self) -> Text:
        return "action_check_sufficient_funds"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # hard-coded balance for tutorial purposes. in production this
        # would be retrieved from a database or an API
        balance = 1000
        transfer_amount = tracker.get_slot("amount")
        has_sufficient_funds = transfer_amount <= balance
        return [SlotSet("has_sufficient_funds", has_sufficient_funds)]


# Minimal custom action code
class create_jira_ticket(Action):
    def name(self):
        return "create_jira_ticket"

    def run(self, dispatcher, tracker, domain):
        #  Get slot values
        title = tracker.get_slot("ticket_title")
        description = tracker.get_slot("ticket_description")
        due_date = tracker.get_slot("ticket_end_date")  # Format: YYYY-MM-DD

        description_adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description or ""
                        }
                    ]
                }
            ]
        }

        # Jira credentials
        jira_domain = os.getenv("JIRA_DOMAIN")  # Your Atlassian domain
        api_token = os.getenv("JIRA_API_TOKEN")  # Store securely
        email = os.getenv("JIRA_EMAIL")  # Your Atlassian email
        project_key = os.getenv("JIRA_PROJECT_KEY")  # Your Jira project key

        # API endpoint
        url = f"{jira_domain}/rest/api/3/issue"

        # Request payload
        payload = {
            "fields": {
                "project": { "key": project_key },
                "summary": title,
                "description": description_adf,
                "duedate": due_date,
                "issuetype": { "name": "Task" }
            }
        }

        # Headers and auth
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        auth = (email, api_token)

        try:
            response = requests.post(url, json=payload, headers=headers, auth=auth)
            print("📩 Jira response:", response.status_code, response.text)
            if response.status_code == 201:
                ticket_key = response.json()["key"]
                dispatcher.utter_message(text=f"✅ Jira ticket created successfully: {ticket_key}")
                return [SlotSet("is_created", True), SlotSet("ticket_key", ticket_key)]
            else:
               
                dispatcher.utter_message(text=f"❌ Failed to create Jira ticket. Status: {response.status_code}")
                return [SlotSet("is_created", False)]

        except Exception as e:
            

            dispatcher.utter_message(text=f"⚠️ Error creating Jira ticket: {str(e)}")
            return [SlotSet("is_created", False)]