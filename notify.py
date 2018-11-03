# -*- coding: utf-8 -*-
"""
Get bus arrival times and SMS them to me.
"""

import json
from datetime import datetime
import requests
from twilio.rest import Client


class CgmInterator(object):
  """Interact with the ЦГМ web API"""

  __TWILIO_ACCOUNT_SID = ""
  __TWILIO_AUTH_TOKEN = ""
  __TWILIO_PHONE_NUMBER = ""

  __WEB_HOST = "https://www.sofiatraffic.bg"
  __API_HOST = "https://api-arrivals.sofiatraffic.bg"
  __API_REFERER = "{}/bg/transport/virtual-tables-by-line?type=bus&line={}&route=1&stop={}"
  __ARRIVALS_API = "{}/api/v1/arrivals/{}/?line={}&type=bus"
  __USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0"
  __TIME_PATTERN = "%Y-%m-%d %H:%M:%S"

  def __init__(self, line_number, stop_number):
    """
    :param int line_number: The number of the line
    :param int stop_number: The ID of the bus stop
    """
    self.line_number = line_number
    self.stop_number = stop_number
    self.stop_name = ""
    self.last_timestamp = None
    self.arrival_times = []

  def __build_headers(self):
    return {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "api-arrivals.sofiatraffic.bg",
    "Origin": self.__WEB_HOST,
    "Referer": self.__API_REFERER.format(self.__WEB_HOST, self.line_number, self.stop_number),
    "User-Agent": self.__USER_AGENT
  }

  def get_next_arrivals(self):
    """Get the list of the next arrival times for the bus"""
    response = requests.get(
      self.__ARRIVALS_API.format(self.__API_HOST, self.stop_number, self.line_number),
      headers=self.__build_headers())

    response = json.loads(response.text)
    self.stop_name = response["name"]
    self.last_timestamp = datetime.strptime(
      response["timestamp_calculated"], self.__TIME_PATTERN)

    if not response["lines"]:
      self.arrival_times = []
    else:
      self.arrival_times = [t["time"] for t in response["lines"][0]["arrivals"]]

  def get_arrivals(self, cutoff=5):
    arrivals = self.arrival_times if len(self.arrival_times) <= cutoff else self.arrival_times[0:cutoff]
    return arrivals

  def __repr__(self):
    return "Arrivals for bus {} @ {}: {}. Collected {}.".format(
      self.line_number, self.stop_number,
      ", ".join(str(t) for t in self.get_arrivals(5)), self.last_timestamp.time())

  def send_sms(self, phone_number, send=False):
    """
    Send the collected bus arrival times as an SMS
    :param phone_number str: The phone number to send an SMS to
    :param send bool: Whether to atually send the message
    """
    message_text = self.__repr__()
    if not send or len(message_text) > 160 or not len(self.arrival_times):
      return None
    client = Client(self.__TWILIO_ACCOUNT_SID, self.__TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=message_text,
        from_=self.__TWILIO_PHONE_NUMBER,
        to=phone_number
    )
    return message.sid

if __name__ == "__main__":
  api = CgmInterator(304, 2688)
  api.get_next_arrivals()
  print(api)
  print(api.send_sms(""))
