from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import datetime as dt


####################################################################################
# carrega portfolio
class ActionPortfolio(Action):
    def name(self):
        return "action_portfolio"

    def run(self, dispatcher, tracker, domain):
        # json = '{"function":"imagegallery","content":[{"image":"url"},{"title":"titulo"},{"description":"descricao"},{"link":"urllink"},{"linktxt":"txtbotao"}]}'
        json = '{"function":"imagegallery","container":"#portifadata"}'
        dispatcher.utter_message(text=f'<<*'+json+'*>>')
        return []


####################################################################################
# verifica o horario para nao dar bom dia quando eh noite no servidor
class ActionDiaTardeNoite(Action):
    def name(self):
        return "action_dia_tarde_noite"

    def run(self, dispatcher, tracker, domain):
        from datetime import datetime
        time = datetime.now()
        h = float( time.strftime("%H") )
        intent = tracker.latest_message["intent"].get("name")

        if (intent == 'diiiia' or intent == 'taaaarde') and (h - 3 >= 18):
            dispatcher.utter_message(text=f"Aqui agora é noite! :)")
        elif (intent == 'diiiia' or intent == 'nooooite') and (h - 3 >= 12) and (h - 3 < 18):
            dispatcher.utter_message(text=f"Aqui agora é de tarde!!!")
        elif (intent == 'taaaarde' or intent == 'nooooite') and (h - 3 >= 6) and (h - 3 < 12):
            dispatcher.utter_message(text=f"Aqui é de manhã! :]")
        elif (intent == 'taaaarde' or intent == 'nooooite') and (h - 3 >= 0) and (h - 3 < 6):
            dispatcher.utter_message(text=f"Aqui é madrugada! :)")

        if (h - 3 < 0):
            dispatcher.utter_message(text=f"Boa noite!")
        elif (h - 3 < 12):
            dispatcher.utter_message(text=f"Bom dia!")
        elif (h - 3 < 18):
            dispatcher.utter_message(text=f"Boa tarde!")
        else:
            dispatcher.utter_message(text=f"Como vai você?")
        return []


####################################################################################
# tipo de usuario
class ActionUserTipo(Action):
    def name(self):
        return "action_user_tipo"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message["intent"].get("name")
        if intent == "sou_desenvolvedor":
            return [SlotSet("user_tipo", "desenvolvedor")]
        elif intent == "sou_cliente":
            return [SlotSet("user_tipo", "cliente")]
        elif intent == "sou_curioso":
            return [SlotSet("user_tipo", "curioso")]
        return []


# ####################################################################################
# # enviar email
# class ActionSendMail(FormAction):
#     def name(self):
#         return "action_send_mail"

#     @staticmethod
#     def required_slots(tracker : Tracker) -> List[Text]:
#         return ["user_email"]

#     def slot_mappings(self):
#         return {
#             "user_email": [
#                 self.from_entity(entity="user_email"),
#                 self.from_text(intent="enter_data"),
#             ]
#         }

#     def validate_email(self, value, dispatcher, tracker, domain):
#         if any(tracker.get_latest_entity_values("user_email")):
#             # entity was picked up, validate slot
#             return {"user_email": value}
#         else:
#             # no entity was picked up, we want to ask again
#             dispatcher.utter_template("utter_no_email", tracker)
#             return {"user_email": None}

#     def submit(self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any]) -> List[Dict]:
#         email = tracker.get_slot("user_email")

#     def run(self, dispatcher, tracker, domain):
#         email = next(tracker.get_latest_entity_values('user_email'), None)  
#         email = tracker.get_slot("user_email")
#         nome = tracker.get_slot("user_name")
#         telefone = tracker.get_slot("user_telefone")
#         mensagem = tracker.get_slot("user_mensagem")

#         subject = "Contato via Hexaquad ("+nome+")"
      
#         body = "Contato para você!\n\nNome: "+nome+"\nE-mail: "+email+"\nTelefone: "+telefone+"\n\n"+mensagem
           
#         sender_email = "hexrocketchat@gmail.com"
#         email = [tracker.get_slot("user_email")]

#         password = "Ijwre732rejkbxz*6y23"

#         # Create a multipart message and set headers
#         message = MIMEMultipart()
#         message["From"] = sender_email
#         message["To"] = 'alexlana@gmail.com'
#         message["Subject"] = subject

#         # Add body to email
#         message.attach(MIMEText(body, "plain"))

#         # Add attachment to message and convert message to string
#         text = message.as_string()

#         # Log in to server using secure context and send email
#         context = ssl.create_default_context()
#         s = smtplib.SMTP(host='smtp.gmail.com', port=587)
#         s.starttls()
#         s.login(sender_email, password)
#         s.sendmail(sender_email, email, message.as_string())
#         return[]    





















class ActionSearchConcerts(Action):
    def name(self):
        return "action_search_concerts"

    def run(self, dispatcher, tracker, domain):
        concerts = [
            {"artist": "Caetano Veloso", "reviews": 4.5},
            {"artist": "Maria Betânia", "reviews": 5.0},
        ]
        description = ", ".join([c["artist"] for c in concerts])
        dispatcher.utter_message(text=f"{description}")
        return [SlotSet("concerts", concerts)]


class ActionSearchVenues(Action):
    def name(self):
        return "action_search_venues"

    def run(self, dispatcher, tracker, domain):
        venues = [
            {"name": "Teatro Nacional", "reviews": 4.5},
            {"name": "Nilson Nelson", "reviews": 5.0},
        ]
        dispatcher.utter_message(text="esses são alguns lugares que encontrei")
        description = ", ".join([c["name"] for c in venues])
        dispatcher.utter_message(text=f"{description}")
        return [SlotSet("venues", venues)]


class ActionShowConcertReviews(Action):
    def name(self):
        return "action_show_concert_reviews"

    def run(self, dispatcher, tracker, domain):
        concerts = tracker.get_slot("concerts")
        dispatcher.utter_message(text=f"shows citados: {concerts}")
        return []


class ActionShowVenueReviews(Action):
    def name(self):
        return "action_show_venue_reviews"

    def run(self, dispatcher, tracker, domain):
        venues = tracker.get_slot("venues")
        dispatcher.utter_message(text=f"lugares citados: {venues}")
        return []


class ActionSetMusicPreference(Action):
    def name(self):
        return "action_set_music_preference"

    def run(self, dispatcher, tracker, domain):
        """Sets the slot 'likes_music' to true/false dependent on whether the user
        likes music"""
        intent = tracker.latest_message["intent"].get("name")

        if intent == "affirm":
            return [SlotSet("likes_music", True)]
        elif intent == "deny":
            return [SlotSet("likes_music", False)]
        return []
