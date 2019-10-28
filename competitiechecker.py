#!/usr/bin/python3

import logging
import re

import pandas as pd
import requests

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import locale
import smtplib
import configparser

__author__ = "Stephan Driesmans"
__copyright__ = """
    Copyright 2019 Stephan Driesmans

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
__license__ = "Apache 2.0"
__version__ = "1.01"
__maintainer__ = "Stephan Driesmans"
__email__ = "stephan.driesmans@gmail.com"
__status__ = "Production"

locale.setlocale(locale.LC_ALL, 'nl_BE')

config = configparser.ConfigParser()
config.read('config.ini')

invoerinterval = int(config.get('interval', 'invoeren'))
bevestiginterval = int(config.get('interval', 'bevestigen'))
seizoen = config.get('seizoen', 'naam')
clubnaam = config.get('club', 'naam')
clubid = config.get('club', 'id')
paswoord = config.get('club', 'wachtwoord')
gmail_user = config.get('mail', 'gebruiker')
gmail_password = config.get('mail', 'wachtwoord')
competitieverantwoordelijke = config.get('mail', 'competitieverantwoordelijke')

logging.basicConfig(filename='competitiechecker.log', filemode='a', format='%(asctime)s - %(message)s',
                    level=logging.INFO)

data = {
    'ctl01$ctl01$container$content$ctl00$cphPage$cphPage$pnlLogin$UserName': clubid,
    'ctl01$ctl01$container$content$ctl00$cphPage$cphPage$pnlLogin$Password': paswoord,
    'ctl01$ctl01$container$content$ctl00$cphPage$cphPage$pnlLogin$LoginButton': 'Inloggen',
    '__EVENTTARGET': '',
    '__EVENTARGUMENT': '',
    '__LASTFOCUS': ''
}


def kapitein(team, soup):
    '''zoek het email adres van de ploegkapitiein op badmintonvlaanderen.be

    :param team: naam van het team
    :param soup: html pagina
    :return: email adres van ploegkapitein
    '''
    link = soup.find('a', href=True, text=team)
    resultaatlink = 'https://www.badmintonvlaanderen.be/sport/' + link['href']
    page = s.get(resultaatlink)
    soup = BeautifulSoup(page.content, features="html5lib")
    link = soup.find('a', href=True, text=team)
    teamlink = 'https://www.badmintonvlaanderen.be/' + link['href']
    page = s.get(teamlink)
    email = re.search(r"[a-z0-9.\-+_]+@[a-z0-9.\-+_]+\.[a-z]+", page.text, re.I).group()
    return (email)


# noinspection PyUnresolvedReferences
def verstuur_email(teamnaam, bericht, link, ontvangers):
    '''Verstuur een mail naar

    :param teamnaam: naam van het team
    :param bericht: details ivm de te bevestigen wedstrijd
    :param link: link naar de pagina op badmintonvlaanderen.be waar je kan invullen/bevestigen
    :param ontvangers: email adressen van de mensen die de mail krijgen
    :return:
    '''

    verzender = gmail_user
    onderwerp = 'Herinnering ' + teamnaam + ' wedstrijduitslag ingeven of bevestigen.'
    body = """\
Beste ploegkapitein,\n\n%s\n\nJe kan de uitslag invullen of bevestigen via volgende link: %s\n\nMet sportieve groeten,\n
    """ % (bericht, link)

    email_tekst = """\
From: %s
To: %s    
Subject: %s

%s
    """ % (verzender, ", ".join(ontvangers), onderwerp, body)
    print(email_tekst)
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_password)
        server.sendmail(verzender, ontvangers, email_tekst)
        server.close()
        logging.info('Email succesvol verstuurd!')
    except:
        logging.error('Er is iets misgegaan...')


logging.info('Start van competitiechecker')

with requests.Session() as s:
    # vraag pagina op en zoek naar de nodige coockies
    page = s.get('https://www.badmintonvlaanderen.be/member/login.aspx?returnurl=%2f')
    soup = BeautifulSoup(page.content, features="html5lib")
    data["__VIEWSTATE"] = soup.select_one("#__VIEWSTATE")["value"]
    data["__VIEWSTATEGENERATOR"] = soup.select_one("#__VIEWSTATEGENERATOR")["value"]
    data["__EVENTVALIDATION"] = soup.select_one("#__EVENTVALIDATION")["value"]

    # login op Badminton Vlaanderen
    s.post('https://www.badmintonvlaanderen.be/member/login.aspx?returnurl=%2f', data=data)

    # zoek naar de link voor de competitie
    page = s.get("https://www.badmintonvlaanderen.be")
    soup = BeautifulSoup(page.content, features="html5lib")
    link = soup.find('a', title=seizoen)
    id = (link.get('href')).split('?')[-1:]

    wedstrijdlink = "https://www.badmintonvlaanderen.be/sport/membermatches.aspx?" + id[0]
    page = s.get(wedstrijdlink)
    soup = BeautifulSoup(page.content, features="html5lib")

    # zoek naar de tabel met wedstrijden
    table = soup.find('table', class_="ruler matches")
    dfs = pd.read_html(str(table), header=0)[0]

    # wandel door de tabel en controleer of de wedstrijd al gespeeld is
    for index, row in dfs.iterrows():
        datum = datetime.strptime(row['Tijdstip'], "%a %d/%m/%Y %H:%M")
        if datum < datetime.today():
            if clubnaam in row['Thuis']:
                logging.info(f'{datum}  {row["Thuis"]} - {row["Uit"]} is gespeeld en is een thuiswedstrijd')
                if str(row['Uitslag']) == 'nan':
                    logging.info('Uitslag is nog niet ingevuld')
                    bericht = (str(row['Tijdstip']) + ' ' + str(row['Thuis']) + " - " + str(
                        row['Uit']) + " is gespeeld en is een thuiswedstrijd.\n")
                    bericht += ('Uiterste datum om te bevestigen: ' + (
                                datum + timedelta(hours=invoerinterval)).strftime("%a %d/%m/%Y %H:%M"))
                    email = [competitieverantwoordelijke]
                    email.append("stephan.driesmans@gmail.com")
                    email.append(kapitein(row['Thuis'], soup))
                    logging.info(f'Verstuur email naar {email}')
                    verstuur_email(row['Thuis'], bericht, wedstrijdlink, email)
                else:
                    logging.info('Uitslag ingevuld')
            if clubnaam in row['Uit']:
                logging.info(f'{datum}  {row["Thuis"]} - {row["Uit"]} is gespeeld en is een uitwedstrijd')
                if str(row['Uitslag']) != 'nan':
                    logging.info('Uitslag is nog niet bevestigd')
                    bericht = (str(row['Tijdstip']) + ' ' + str(row['Thuis']) + " - " + str(
                        row['Uit']) + " is gespeeld en is een uitwedstrijd.\n")
                    bericht += ('Uiterste datum om te bevestigen: ' + (
                                datum + timedelta(hours=bevestiginterval)).strftime("%a %d/%m/%Y %H:%M"))
                    email = [competitieverantwoordelijke]
                    email.append("voorzitter@amateursbadminton.be")
                    email.append(kapitein(row['Uit'], soup))
                    logging.info(f'Verstuur email naar {email}')
                    verstuur_email(row['Uit'], bericht, wedstrijdlink, email)
                else:
                    logging.info('Uitslag is nog niet ingevuld door tegenpartij')
