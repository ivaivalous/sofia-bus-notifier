# sofia-bus-notifier

I take the bus to go to work or return home from it.

I used to check manually when my bus is going to arrive next, but thought why not automate it.

So I wrote this simple Python script to fetch the next few arrival times for my bus at my stop and send them to me via SMS using Twilio.

I have a couple of Jenkins jobs on my private server that run 15 minutes before I'm supposed to leave in either way, so I have to do nothing by myself.

```groovy
node ("master") {
    stage ("Checkout") {
        git url: "https://github.com/ivaivalous/sofia-bus-notifier"
    }
    stage ("Send SMS") {
        sh """
            export TWILIO_ACCOUNT_SID=<SID>
            export TWILIO_AUTH_TOKEN=<TOKEN>
            export TWILIO_PHONE_NUMBER=<FROM NUMBER>
            python3 notify.py <LINE> <STOP> <MY PHONE>
        """
    }
}
```

Notes:
 - The script is for the Sofia, Bulgaria bus API
 - Using their bus API violates their terms of service, so run the script at your own risk
 - Their API is often very unreliable, so buses may not arrive at the reported times, or the API might return nothing at all for a given line for some times.
 