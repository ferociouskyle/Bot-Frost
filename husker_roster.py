# Source: http://www.huskers.com/SportSelect.dbml?DB_OEM_ID=100&SPID=22&SPSID=4&KEY=&Q_SEASON=2019
from bs4 import BeautifulSoup
import requests
import sportsreference
from sportsreference.ncaaf.teams import Teams

husker_roster_url = 'http://www.huskers.com/SportSelect.dbml?DB_OEM_ID=100&SPID=22&SPSID=4&KEY=&Q_SEASON='


async def download_roster(year=2019):
    print("***\nDownload Roster")


    print("***")
