# -*- coding: utf-8 -*-
"""
Get bus arrival times and SMS them to me.
"""

import os
import json
import sys
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

  def __get_twilio_credentials(self):
    """
    Get the Twilio access credentials - try the TWILIO_ACCOUNT_SID and
    TWILIO_AUTH_TOKEN environment variables, and if missing default
    to the constants with the same names.
    :return (str, str): Twilio account SID and auth token
    """
    return os.getenv("TWILIO_ACCOUNT_SID", self.__TWILIO_ACCOUNT_SID), \
      os.getenv("TWILIO_AUTH_TOKEN", self.__TWILIO_AUTH_TOKEN)

  def __get_twilio_phone_number(self):
    """
    Get the Twilio send-from phone number: try the TWILIO_PHONE_NUMBER
    environment variable, and if missing, default to the __TWILIO_PHONE_NUMBER
    constant.
    :return str: The phone number to send from
    """
    return os.getenv("TWILIO_PHONE_NUMBER", self.__TWILIO_PHONE_NUMBER)

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
    if not response:  # The response would be empty at times when the line is not running
      return
    self.stop_name = response["name"]
    self.last_timestamp = datetime.strptime(
      response["timestamp_calculated"], self.__TIME_PATTERN)

    if not response["lines"]:
      self.arrival_times = []
    else:
      self.arrival_times = [t["time"] for t in response["lines"][0]["arrivals"]]

  def get_arrivals(self, cutoff=5):
    arrivals = self.arrival_times if len(
      self.arrival_times) <= cutoff else self.arrival_times[0:cutoff]
    return arrivals
  
  @staticmethod
  def __remove_seconds(arrivals):
    return [arrival.split(":")[:1] for arrival in arrivals]

  def __repr__(self):
    if not self.last_timestamp:
      return "Arrivals for bus {} @ {}.".format(self.line_number, self.stop_number)
    arrivals = self.__remove_seconds(self.get_arrivals(5))
    return "Arrivals for bus {} @ {}: {}. Collected {}.".format(
      self.line_number, self.stop_number,
      ", ".join(str(t) for t in arrivals), self.last_timestamp.time())

  def send_sms(self, phone_number, send=False):
    """
    Send the collected bus arrival times as an SMS
    :param phone_number str: The phone number to send an SMS to
    :param send bool: Whether to atually send the message
    """
    message_text = self.__repr__()
    if not send or len(message_text) > 160 or not len(self.arrival_times):
      return None
    client = Client(*self.__get_twilio_credentials())
    message = client.messages.create(
        body=message_text,
        from_=self.__get_twilio_phone_number(),
        to=phone_number
    )
    return message.sid

if __name__ == "__main__":
  if len(sys.argv) != 4:
    print("Usage: notify.py <line number> <stop number> <phone number>")
    exit(1)

  line, stop, phone = sys.argv[1:]
  try:
    line = int(line)
    stop = int(stop)
  except ValueError:
    print("Line and stop numbers must in fact be numbers.")
    exit(1)

  api = CgmInterator(line, stop)
  api.get_next_arrivals()
  print(api)
  print(api.send_sms(phone, True))
