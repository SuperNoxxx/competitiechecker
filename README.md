# Competitiechecker

Python program to check unconfirmed competition matches on badmintonvaanderen.be and to send mails to teamcaptains if there are unconfirmed entries

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.
clone this repostory, modify the following variables:
```
# clubnaam zoals in de ploegnamen vermeld
clubnaam = "Amateurs"

# login gegevens
clubid = "c10012"
paswoord = "xxxxxxxxxxx"

# connectiegegevens google mailserver
gmail_user = 'xxxxxxxxxxxx@gmail.com'
gmail_password = 'xxxxxxxxxxxxxxx'

# bijkomende contactpersoon voor mails
competitieverantwoordelijke = "xxxxxxxxxxxxxxxxxxxxxxxx"
```
### Prerequisites

At least python 3.6 is required

Install following modules:
* pandas
* requests
* bs4
* html5
* liblxml
```
pip install pandas
pip install requests
pip install bs4
pip install html5lib
pip install lxml
```
## Authors

* **Stephan Driesmans** - *Initial work* - https://github.com/SuperNoxxx

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE.md) file for details
