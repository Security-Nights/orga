#!/usr/bin/env python3

from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from getpass import getpass
from icalendar import Calendar, Event
from smtplib import SMTP
from uuid import uuid4
from zoneinfo import ZoneInfo
import gnupg

msa_address = 'localhost'
msa_port = 587
username = input('MSA username: ')
password = getpass('MSA password: ')

gpghome_path = '$HOME/.gnupg'
recipients_file = './email_recipients.txt'
sender = {
    'name': 'Security Nights',
    'address': 'security.nights@localhost',
    'key_id': '1337'
}

event_dt = datetime(year = 2022, month = 9, day = 8, hour = 19, tzinfo = ZoneInfo('Europe/Berlin'))
event_location = {
    'name': 'SysEleven',
    'place': 'Boxhagener Str. 79, 10245 Berlin',
    'map': 'https://openstreetmap.org/node/2825036679'
}
event_url = 'https://meetup.com/berlin-internet-security-group/events/287899582'
event_id = '22/Sep'
event_topic = 'devsetup; AWS pentest; TLS & MitM'
event_image_file = './banner.jpeg'
event_tldr = '''
Join the next Security Night on September 8 from 7 pm CEST at SysEleven: Boxhagener Str. 79, 10245 Berlin. Three speakers are ready to share their talks with you:

1. devsetup by Pierre Pronchery
2. Penetration Testing on AWS by Lisa Wang
3. TLS and Man in the Middle (foundational) by Akendo
'''.lstrip()

invitation = '''
Dear Berlin Security Community,

TL;DR | '''.lstrip() + event_tldr + '\n' + event_url + '''

--> WHAT TO EXPECT

After months of silence, it is finally enough. We should talk about all the things happening around us. Let us meet again in-person and discuss! So we can get back to normal, hopefully...

This time, we have three great speakers on offer: Pierre about a nice tool he has developed, Lisa about her fresh Bachelor's thesis on pentesting and Akendo about the foundations of MitM with TLS. And Akendo has also joined our organization team -- welcome!

A big thanks to SysEleven and especially to Kenny and Joseph for providing location, food and drinks for the night. Their space for talks is great and they hosted a series of really interesting tech meetups.

--> THE TALKS

(1) "devsetup: local development environment and security tools for any platform" by Pierre Pronchery:
The pkgsrc project is the official source for third-party software packages for the NetBSD Operating System. However, given the passion of NetBSD developers for portability, pkgsrc supports over 20 different platforms -- including macOS, where it can advantageously replace Homebrew. During this presentation, we will see how pkgsrc can therefore be used easily anywhere thanks to a single script, "devsetup", and that it also offers a number of security tools.

(2) "Penetration Testing Approaches on Selected AWS Services" by Lisa Wang:
In this presentation, we discuss the results of a Bachelor's thesis about practical penetration tests that are carried out on selected AWS services. It should be illustrated which approaches of penetration tests are possible with the selected AWS services and which security measures could minimize the attack surface.

(3) "The TLS and the Man in the Middle -- a brief overview and a small demonstration" by Akendo:
I recently was confronted with a fairly odd problem. To put it simple: do not trust a trustworthy certificate, and instead replace it with a trustworthy certificate upfront instead. Here's the catch, it wasn't possible to replace the actual certificate of the service. In this presentation, I want to demonstrate how odd problems require sometimes odd solutions.

--> THE NIGHT

We are happy to invite you to our next Security Night on September 8 at SysEleven's offices: Boxhagener Str. 79, 10245 Berlin (https://openstreetmap.org/node/2825036679). Our agenda for the night:

7:00 pm -- Welcome
7:10 pm -- Pierre Pronchery
7:30 pm -- Lisa Wang
7:50 pm -- Akendo
8:10 pm -- Q&A
9:00 pm -- Closing

Attendance is free. Emergency phone number, in case of any problems: +4917634326568. Please register at Meetup, so we can plan accordingly: https://meetup.com/berlin-internet-security-group/events/287899582

Please note the regulations regarding COVID-19 on the day of the event. If you want, you can of course wear a mask and/or register on site via the Corona-Warn-App.

See you there!

--> CONTACT US

Berlin Security Nights are organized by Martin, Akendo and Hendrik as a contribution to the scene. We like bringing great people together. You can find us offline at our nights or online on Slack:
https://join.slack.com/t/berlin-infosec/shared_invite/enQtNTY3ODU0OTU5NjcwLTAzMmZiNDQxNDk0NzE4NGJjOTE0ODJiOWRkMGY2Y2QwZTUxYzgzYTVlMGQ3YTllNjQ0YjFiNzVlYjZiMWU2MWY

Kind regards,
Martin

PS: We are always looking for interesting talks and projects. If you have a talk proposal, an interesting project or something you would love to share with the community, please write us an email or reach out on Slack.

-- 
M. G. Falkus, IT-Sicherheitsingenieur
Tel.: +4917634326568

To unsubscribe from this list, please reply to this email with "unsubscribe" in the subject or as message body.
''' + '\n'

def gen_cal_event(id, topic, dt, location, tldr, url):
    calendar = Calendar()
    calendar.add('PRODID', '-//mgf//NONSGML sendmail v0.1//EN')
    calendar.add('VERSION', '2.0')
    event = Event()
    event.add('SUMMARY', 'Security Night ' + id + ': ' + topic)
    event.add('UID', uuid4())
    event.add('DTSTAMP', datetime.utcnow())
    event.add('DTSTART', dt)
    event.add('DTEND', dt + timedelta(hours = 2)) ## DURATION
    event.add('LOCATION', location['name'] + ', ' + location['place'])
    event.add('DESCRIPTION', tldr)
    event.add('URL', url)
    calendar.add_component(event)
    return calendar.to_ical()

def gen_message(sender, event_id, event_topic, event_dt, event_location, event_image, invitation, ical, gpghome_path):
    # message with headers:
#    message = MIMEMultipart(_subtype = 'signed', protocol = 'application/pgp-signature', micalg = 'pgp-sha512')
    message = MIMEMultipart() ##
    message['Date'] = datetime.utcnow().strftime('%a, %-d %b %Y %X +0000')
    message['From'] = sender['name'] + ' <' + sender['address'] + '>'
    message['Subject'] = '[Security Nights] Invitation ' + event_id + ': ' + event_topic + ' -- ' + event_dt.strftime('%A, %B %-d, %Y, %-I %p %Z') + ' @ ' + event_location['name']
#    # body ("multipart/mixed"):
#    body = MIMEMultipart()
#    body.attach(MIMEText(invitation.replace('\n', '\r\n'), _charset = 'utf-8'))
    message.attach(MIMEText(invitation.replace('\n', '\r\n'), _charset = 'utf-8')) ##
    part_calendar = MIMEText(ical.decode(), _subtype = 'calendar', _charset = 'utf-8')
    part_calendar['Content-Disposition'] = 'attachment; filename="SN_' + event_id.replace('/', '-') + '.ics"'
#    body.attach(part_calendar)
    message.attach(part_calendar) ##
    part_image = MIMEImage(event_image, _subtype = 'jpeg')
    part_image['Content-Disposition'] = 'attachment; filename="SN_banner.jpeg"'
#    body.attach(part_image)
    message.attach(part_image) ##
#    message.attach(body)
#    # PGP signature:
#    gpg = gnupg.GPG(gnupghome = gpghome_path)
#    gpg.encoding = 'utf-8'
#    message.attach(MIMEApplication(str(gpg.sign(body.as_bytes(), keyid = sender['key_id'], detach = True)), _subtype = 'pgp-signature'))
    return message

def main():
    recipients = []
    ical = gen_cal_event(event_id, event_topic, event_dt, event_location, event_tldr, event_url)
    with open(event_image_file, 'rb') as f:
        message = gen_message(sender, event_id, event_topic, event_dt, event_location, f.read(), invitation, ical, gpghome_path)
    with open(recipients_file) as f:
        for line in f.readlines():
            recipients.append(line.rstrip())
    with SMTP(host = msa_address, port = msa_port) as smtp_object:
        smtp_object.starttls()
        smtp_object.login(user = username, password = password)
        try:
            result = smtp_object.send_message(from_addr = sender['address'], to_addrs = recipients, msg = message)
        except Exception as e:
            print('Done, but _all_ recipients refused: ' + str(e))
            return -1
        if len(result) >= 0:
            print('Done, and ' + str(len(result)) + ' recipient(s) refused.')
            for item in result.items():
                print(str(item))
    return 0

if __name__ in [ '__main__', '__builtin__' ]:
    main()

# EOF.
