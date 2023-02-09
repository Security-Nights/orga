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
from os.path import abspath
from smtplib import SMTP
from uuid import uuid4
from yaml import safe_load
from zoneinfo import ZoneInfo

def gen_text(talks, space, time_start, duration, tldr, invitation, meetup_url, contacts):
    text = 'Dear Berlin Security Community,\n\n'
    text += 'TL;DR | ' + tldr + '\n\n'
    text += '--> WHAT TO EXPECT\n\n'
    text += invitation + '\n\n'
    text += '--> THE TALKS\n\n'
    for talk_id in list(talks):
        text += '(' + str(talk_id) + ') "' + talks[talk_id]['title'] + '"'
        text += ' by ' + talks[talk_id]['name'] + ':\n'
        text += talks[talk_id]['abstract'] + '\n\n'
    text += '--> THE NIGHT\n\n'
    text += 'We are happy to invite you to our next Security Night conference'
    text += ' on ' + time_start.strftime('%B %-d')
    text += ' at ' + space['name'] + ': ' + space['address'] + ' (' + space['map_url'] + ').'
    text += ' Our agenda for this Night:\n\n'
    time_current = time_start
    text += time_current.strftime('%I:%M %p') + ' -- Welcome\n'
    time_current += timedelta(minutes = 10)
    for talk_id in list(talks):
        text += time_current.strftime('%I:%M %p') + ' -- ' + talks[talk_id]['name'] + '\'s talk\n'
        time_current += timedelta(minutes = 20)
        if talk_id < len(list(talks)):
            time_current += timedelta(minutes = 10)
    text += time_current.strftime('%I:%M %p') + ' -- Networking\n'
    time_current = time_start + timedelta(minutes = duration)
    text += time_current.strftime('%I:%M %p') + ' -- Closing\n\n'
    text += 'Attendance is free. Emergency phone number, in case of any problems: ' + ', '.join(contacts) + '.'
    text += ' Please register at Meetup, so we can plan accordingly: ' + meetup_url + '\n\n'
    text += '--> CONTACT US\n\n'
    text += 'Berlin Security Nights are organized by Akendo, Hendrik and Martin as a contribution to the scene.'
    text += ' We like bringing great people together. You can find us offline at our Nights or online on Slack:'
    text += ' https://join.slack.com/t/berlin-infosec/shared_invite/enQtNTY3ODU0OTU5NjcwLTAzMmZiNDQxNDk0NzE4NGJjOTE0ODJiOWRkMGY2Y2QwZTUxYzgzYTVlMGQ3YTllNjQ0YjFiNzVlYjZiMWU2MWY\n\n'
    text += 'See you around!\n\n'
    text += 'Your Security Night Owls,\n'
    text += 'Akendo, Hendrik, Martin\n\n'
    text += 'PS: We are always looking for interesting talks and projects.'
    text += ' If you have a talk proposal, an interesting project or something you would love to share with the community, please write us an email or reach out on Slack.\n\n'
    text += '-- \nTo unsubscribe from the mailing list, please reply to this email with "unsubscribe" in the subject or just as the message body.\n'
    return text

def get_input_data():
    event = {}
    event['id'] = input('Please input the event ID, e.g. "2023/March": ')
    file_event = '../' + event['id'] + '/event.yaml'
    file_talks = '../' + event['id'] + '/talks.yaml'
    file_invitation = '../' + event['id'] + '/invitation.txt'
    file_output = '../' + event['id'] + '/email_body.txt'
    print('Haye you prepared the following files?')
    print('--> ' + abspath(file_event))
    print('--> ' + abspath(file_talks))
    print('--> ' + abspath(file_invitation))
    if input('If so, type "yes": ').lower() != 'yes':
        raise Exception('Event data not yet prepared')
    with open(file_event) as f:
        event.update(safe_load(f))
    event['time'] = datetime.strptime(event['time'], '%Y-%m-%dT%H:%M:%S%z')
    with open(file_talks) as f:
        event['talks'] = safe_load(f)
    event['tldr'] = 'Join our next Security Night conference'
    event['tldr'] += ' on ' + event['time'].strftime('%B %-d from %-I %p %Z')
    event['tldr'] += ' at ' + event['space']['name'] + ': ' + event['space']['address'] + '.'
    event['tldr'] += ' The following speakers are ready to share their insights with you:\n'
    for talk_id in list(event['talks']):
        event['tldr'] += '\n' + str(talk_id) + '. "' + event['talks'][talk_id]['title'] + '"'
        event['tldr'] += ' by ' + event['talks'][talk_id]['name']
    with open(file_invitation) as f:
        event['text'] = gen_text(
            event['talks'],
            event['space'],
            event['time'],
            event['duration'],
            event['tldr'],
            f.read(),
            event['meetup_url'],
            event['contacts']
        )
    with open(file_output, 'w') as f:
        f.write(event['text'])
    print('Does the following file represent your intended email?')
    print('--> ' + abspath(file_output))
    if input('If so, type "yes": ').lower() != 'yes':
        raise Exception('Generated email body inappropriate')
    print('Nice! Please input some more data:')
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
        'event': event
    }

def gen_cal_event(id, topic, space, time, duration, url, text):
    calendar = Calendar()
    calendar.add('PRODID', '-//mgf//NONSGML sendmail v0.1//EN')
    calendar.add('VERSION', '2.0')
    event = Event()
    event.add('UID', uuid4())
    event.add('DTSTAMP', datetime.utcnow())
    event.add('SUMMARY', 'Security Night ' + id + ': ' + topic)
    event.add('LOCATION', space['name'] + ', ' + space['address'])
    event.add('DTSTART', time)
    event.add('DTEND', time + timedelta(minutes = duration))
    event.add('URL', url)
    event.add('DESCRIPTION', text)
    calendar.add_component(event)
    return calendar.to_ical()

def gen_message(sender, event, image):
    message = MIMEMultipart()
    message['Date'] = datetime.utcnow().strftime('%a, %-d %b %Y %X +0000')
    message['From'] = sender['name'] + ' <' + sender['address'] + '>'
    subject = '[Security Nights] Invitation ' + event['id'] + ': ' + event['topic']
    subject += ' -- ' + event['time'].strftime('%A, %B %-d, %Y, %-I %p %Z') + ' @ ' + event['space']['name']
    message['Subject'] = subject
    message.attach(MIMEText(event['text'].replace('\n', '\r\n'), _charset = 'utf-8'))
    part_calendar = MIMEText(
        gen_cal_event(
            event['id'],
            event['topic'],
            event['space'],
            event['time'],
            event['duration'],
            event['meetup_url'],
            event['tldr']
        ).decode(),
        _subtype = 'calendar',
        _charset = 'utf-8'
    )
    part_calendar['Content-Disposition'] = 'attachment; filename="SN_' + event['id'].replace('/', '-') + '.ics"'
    message.attach(part_calendar)
    part_image = MIMEImage(image, _subtype = 'jpeg')
    part_image['Content-Disposition'] = 'attachment; filename="SN_banner.jpeg"'
    message.attach(part_image)
    return message

def main():
    data = get_input_data()
    recipients = []
    with open('banner.jpeg', 'rb') as f:
        message = gen_message(data['sender'], data['event'], f.read())
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
