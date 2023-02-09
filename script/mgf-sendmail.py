#!/usr/bin/env python3

#
# File: mgf-sendmail.py
# Author: Martin G. Falkus <martin@mgfalkus.de>
#

from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from getpass import getpass
from icalendar import Calendar, Event
from smtplib import SMTP
from uuid import uuid4
from yaml import safe_load
from zoneinfo import ZoneInfo

header = '''
Dear Berlin Security Community,

TL;DR | Join the next Security Night on September 2nd from 7 pm CEST at c-base:  Rungestraße 20 10179 Berlin. Three speakers are ready to share their talks with you:

1. Something Something hashes by pspacecomplete
2. Soemthing Somethin Windows Server hacking by Sven
3. Somethin Somethin SSHFP ny Neef

--> WHAT TO EXPECT
'''.lstrip()

footer = '''
--> THE TALKS

(1) "TBD"

(2) "TBD"

(3) "TBD"

--> THE NIGHT

We are happy to invite you to our next Security Night on September 8 at SysEleven's offices: Boxhagener Str. 79, 10245 Berlin (https://openstreetmap.org/node/2825036679). Our agenda for the night:

7:00 pm -- Welcome
7:10 pm -- TBD
7:30 pm -- TBD
7:50 pm -- TBD
8:10 pm -- Q&A
9:00 pm -- Closing

Attendance is free. Emergency phone number, in case of any problems: +4917634326568. Please register at Meetup, so we can plan accordingly: https://meetup.com/berlin-internet-security-group/events/287899582

Please note the regulations regarding COVID-19 on the day of the event. If you want, you can of course wear a mask and/or register on site via the Corona-Warn-App.

See you there!

--> CONTACT US

Berlin Security Nights are organized by Martin, Akendo and Hendrik as a contribution to the scene. We like bringing great people together. You can find us offline at our nights or online on Slack:
https://join.slack.com/t/berlin-infosec/shared_invite/enQtNTY3ODU0OTU5NjcwLTAzMmZiNDQxNDk0NzE4NGJjOTE0ODJiOWRkMGY2Y2QwZTUxYzgzYTVlMGQ3YTllNjQ0YjFiNzVlYjZiMWU2MWY

Your (lexicographically ordered) Security Night Owls
Akendo, Hendrik, Martin

PS: We are always looking for interesting talks and projects. If you have a talk proposal, an interesting project or something you would love to share with the community, please write us an email or reach out on Slack.
'''.lstrip()

def get_input_data():
    event_data = {}
    print('Please make sure the event\'s YAML data is in place!')
    event_data['id'] = input('Event ID, e.g. "2023/March": ')
    with open('../' + event_data['id'] + '/event.yaml') as f:
        event_data.update(safe_load(f))
    event_data['time'] = datetime.strptime(event_data['time'], '%Y-%m-%dT%H:%M:%S%z')
    with open('../' + event_data['id'] + '/talks.yaml') as f:
        event_data['talks'] = safe_load(f)
    with open('../' + event_data['id'] + '/invitation.txt') as f:
        event_data['invitation'] = header + '\n'
        event_data['invitation'] += f.read() + '\n'
        event_data['invitation'] += footer + '\n'
    return {
        'server': {
            'address': input('Server address: '),
            'port': input('TCP port: '),
            'username': input('Username: '),
            'password': getpass('Password: ')
        },
        'sender': {
            'name': input('Sender name: '),
            'address': input('Email address: ')
        },
        'event': event_data
    }

def gen_cal_event(id, topic, space, time, duration, url, text):
    calendar = Calendar()
    calendar.add('PRODID', '-//mgf//NONSGML sendmail v0.1//EN')
    calendar.add('VERSION', '2.0')
    event = Event()
    event.add('SUMMARY', 'Security Night ' + id + ': ' + topic)
    event.add('UID', uuid4())
    event.add('DTSTAMP', datetime.utcnow())
    event.add('DTSTART', time)
    event.add('DTEND', time + timedelta(minutes = duration))
    event.add('LOCATION', space['name'] + ', ' + space['address'])
    event.add('DESCRIPTION', text)
    event.add('URL', url)
    calendar.add_component(event)
    return calendar.to_ical()

def gen_message(sender, event, image, ical):
    subject = '[Security Nights] Invitation ' + event['id'] + ': ' + event['topic']
    subject += ' -- ' + event['time'].strftime('%A, %B %-d, %Y, %-I %p %Z') + ' @ ' + event['space']['name']
    message = MIMEMultipart()
    message['Date'] = datetime.utcnow().strftime('%a, %-d %b %Y %X +0000')
    message['From'] = sender['name'] + ' <' + sender['address'] + '>'
    message['Subject'] = subject
    message.attach(MIMEText(event['invitation'].replace('\n', '\r\n'), _charset = 'utf-8'))
    part_calendar = MIMEText(ical.decode(), _subtype = 'calendar', _charset = 'utf-8')
    part_calendar['Content-Disposition'] = 'attachment; filename="SN_' + event['id'].replace('/', '-') + '.ics"'
    message.attach(part_calendar)
    part_image = MIMEImage(image, _subtype = 'jpeg')
    part_image['Content-Disposition'] = 'attachment; filename="SN_banner.jpeg"'
    message.attach(part_image)
    return message

def main():
    data = get_input_data()
    tldr = 'Join our next Security Night'
    tldr += ' on ' + data['event']['time'].strftime('%B %-d from %-I %p %Z')
    tldr += ' at ' + data['event']['space']['name'] + ': ' + data['event']['space']['address'] + '.'
    tldr += ' The following speakers are ready to share their talks with you:\n'
    for talk_id in list(data['event']['talks']):
        tldr += '\n' + str(talk_id) + '. "' + data['event']['talks'][talk_id]['title'] + '"'
        tldr += ' by ' + data['event']['talks'][talk_id]['name']
    with open('banner.jpeg', 'rb') as f:
        message = gen_message(
            data['sender'],
            data['event'],
            f.read(),
            gen_cal_event(
                data['event']['id'],
                data['event']['topic'],
                data['event']['space'],
                data['event']['time'],
                data['event']['duration'],
                data['event']['meetup_url'],
                tldr
            )
        )
    recipients = []
    with open('recipients.txt') as f:
        for line in f.readlines():
            recipients.append(line.rstrip())
    with SMTP(host = data['server']['address'], port = data['server']['port']) as s:
        s.starttls()
        s.login(user = data['server']['username'], password = data['server']['password'])
        try:
            result = s.send_message(from_addr = data['sender']['address'], to_addrs = recipients, msg = message)
        except Exception as e:
            print('Done, but _all_ recipients refused: ' + str(e))
            return -1
        if len(result) >= 0:
            print('Done, ' + str(len(result)) + ' recipient(s) refused.')
            for item in result.items():
                print(str(item))
    return 0

if __name__ in [ '__main__', '__builtin__' ]:
    main()

# EOF.
