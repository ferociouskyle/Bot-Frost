import discord
import function_helper
import requests
import json
import datetime
import pandas
import crystal_balls
import os, sys, inspect
import importlib
from bs4 import BeautifulSoup
import re
from discord.ext import commands

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parrentdir = os.path.dirname(currentdir)
sys.path.insert(0, parrentdir)
import config

wrong_channel_text='The command you sent is not authorized for use in this channel.'
welcome_footer='HusekrBot welcomes you!'
huskerbot_footer="Generated by HuskerBot"

authorized_to_quit = [440639061191950336, 443805741111836693, 189554873778307073, 339903241204793344, 606301197426753536]
emoji_list = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']
long_positions = {'PRO' : 'Pro-Style Quarterback',
                  'DUAL': 'Dual-Threat Quarterback',
                  'APB' : 'All-Purpose Back',
                  'RB' : 'Running Back',
                  'FB' : 'Fullback',
                  'WR' : 'Wide Receiver',
                  'TE' : 'Tight End',
                  'OT' : 'Offensive Tackle',
                  'OG' : 'Offensive Guard',
                  'OC' : 'Center',
                  'SDE' : 'Strong-Side Defensive End',
                  'WDE' : 'Weak-Side Defensive End',
                  'DT' : 'Defensive Tackle',
                  'ILB' : 'Inside Linebacker',
                  'OLB' : 'Outside Linebacker',
                  'CB' : 'Cornerback',
                  'S' : 'Safety',
                  'ATH' : 'Athlete',
                  'K' : 'Kicker',
                  'P' : 'Punter',
                  'LS' : 'Long Snapper',
                  'RET' : 'Returner'
                  }
globalRate = 3
globalPer = 30

try:
    with open('team_ids.json', 'r') as fp:
        team_ids = json.load(fp)
except:
    print("Error opening team_ids.json")


# TODO Look at and revamp
async def check_last_run():
    """ Check when the last time the JSON was pulled. """
    now = datetime.datetime.now()
    temp_check = config.last_run
    check = pandas.to_datetime(temp_check) + datetime.timedelta(minutes=crystal_balls.CB_REFRESH_INTERVAL)

    print("***\nNow: {}\nTemp Check: {}\nCheck: {}\nNow > Check: {}\n***".format(now, temp_check, check, now > check))

    if now > check:
        print("Last time the JSON was pulled exceeded threshold")

        # if ctx: await ctx.send("The crystal ball database is stale. Updating now; standby...")

        crystal_balls.move_cb_to_list_and_json(json_dump=True)

        f = open('config.py', 'r')
        lines = f.readlines()
        temp = ""
        for l in lines:
            if not "last_run" in l:
                temp = temp + l
        temp = temp + "last_run = \'{}\'\n".format(datetime.datetime.now())
        f.close()

        f = open("config.py", "w+")
        f.write(temp)
        f.close()

        importlib.reload(config)

        # if ctx: await ctx.send("The crystal ball database is fresh and ready to go! {} entries were collected.".format(len(crystal_balls.cb_list)))
    else:
        # await ctx.send("The crystal ball database is already fresh.")
        if len(crystal_balls.cb_list) <= 1:
            crystal_balls.load_cb_to_list()


async def parse_search(search, channel):
    year = search['Year']
    player = search['Player']
    first_name = player['FirstName']
    last_name = player['LastName']
    position = player['PrimaryPlayerPosition']['Abbreviation']
    if position in long_positions:
        position = long_positions[position]
    hometown = player['Hometown']
    state = hometown['State']
    city = hometown['City']
    height = player['Height'].replace('-', "'") + '"'
    weight = player['Weight']
    high_school = player['PlayerHighSchool']['Name']
    image_url = player['DefaultAssetUrl']
    composite_rating = player['CompositeRating']
    if composite_rating is None:
        composite_rating = 'N/A'
    else:
        composite_rating = player['CompositeRating'] / 100
    composite_star_rating = player['CompositeStarRating']
    national_rank = player['NationalRank']
    if national_rank is None:
        national_rank = 'N/A'
    position_rank = player['PositionRank']
    if position_rank is None:
        position_rank = 'N/A'
    state_rank = player['StateRank']
    if state_rank is None:
        state_rank = 'N/A'
    player_url = player['Url']
    # global profile_url
    config.profile_url = player_url

    # Grab the croot's Twitter handle from their player_url page
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
    page = None
    try:
        page = requests.get(url=player_url, headers=headers)
    except requests.exceptions.RequestException as e:
        print(e)

    soup = BeautifulSoup(page.text, 'html.parser')
    re_pattern = "data-username=\".{0,}?\""
    twitter_raw = soup.find_all('div', class_='main-div clearfix')
    if twitter_raw:
        twitter_raw = str(twitter_raw[0])
        twitter_raw2 = re.findall(re_pattern, twitter_raw)
        if len(twitter_raw2) > 0:
            twitter_handle = twitter_raw2[0]
            twitter_handle = twitter_handle.replace("@","")
            twitter_handle = twitter_handle[15:-1]
            twitter_url = "https://twitter.com/" + twitter_handle
        else:
            twitter_handle = "N/A"
            twitter_url = ""
    else:
        twitter_handle = "Unable to locate"
        twitter_url = ""
        print("really not sure")
    # Attempting to get twitter handle from player_url

    stars = ''
    for i in range(int(composite_star_rating)):
        stars += '\N{WHITE MEDIUM STAR}'

    # Check if they are committed. It's a little different with signed players.
    commit_status = search['HighestRecruitInterestEventType']
    if commit_status == 'HardCommit' or commit_status == 'SoftCommit':
        commit_status = 'Committed'
    else:
        commit_status = 'Uncommitted'
    if type(search['SignedInstitution']) is int:
        commit_status = 'Signed'
    title = '{} **{} {}, {} {}**'.format(stars, first_name, last_name, year, position)

    # Now that composite rating can be str or float, we need to handle both cases. Also, don't want the pound sign in front of N/A values.
    if type(composite_rating) is str:
        body = '**Player Bio**\nHome Town: {}, {}\nHigh School: {}\nHeight: {}\nWeight: {}\n\n**247Sports Info**\nComposite Rating: {}\nProfiles: [Click Me]({})\n\n**Twitter**\n[@{}]({})\n\n'.format(city, state, high_school, height, int(weight), composite_rating, player_url, twitter_handle, twitter_url)
        rankings = '**Rankings**\nNational: #{}\nState: #{}\nPosition: #{}\n'.format(national_rank, state_rank, position_rank)
    else:
        body = '**Player Bio**\nHome Town: {}, {}\nHigh School: {}\nHeight: {}\nWeight: {}\n\n**247Sports Info**\nComposite Rating: {:.4f}\nProfile: [Click Me]({})\n\n**Twitter**\n[@{}]({})\n\n'.format(city, state, high_school, height, int(weight), composite_rating, player_url, twitter_handle, twitter_url)
        rankings = '**Rankings**\nNational: #{}\nState: #{}\nPosition: #{}\n'.format(national_rank, state_rank, position_rank)

    # Create a recruitment status string. If they are committed, use our scraped json team_ids dictionary to get the team name from the id in the committed team image url.
    # I've found that if a team does not have an image on 247, they use a generic image with 0 as the id. Also if the image id is not in the dictionary, we want to say Unknown.
    recruitment_status = 'Currently {}'.format(commit_status)
    if commit_status == 'Committed' or commit_status == 'Signed':
        school_id = str(search['CommitedInstitutionTeamImage'].split('/')[-1].split('.')[0])
        if school_id == '0' or school_id not in team_ids:
            school = 'Unknown'
        else:
            school = team_ids[school_id]
        if school == 'Nebraska':
            school += ' 💯:corn::punch:'
        recruitment_status += ' to {}'.format(school)
    recruitment_status = '**' + recruitment_status + '**\n\n'

    crootstring = recruitment_status + body + rankings
    message_embed = discord.Embed(name="CrootBot", color=0xd00000)
    message_embed.add_field(name=title, value=crootstring, inline=False)
    # Don't want to try to set a thumbnail for a croot who has no image on 247
    if image_url != '/.':
        message_embed.set_thumbnail(url=image_url)
    message_embed.set_footer(text=huskerbot_footer)
    await channel.send(embed=message_embed)

    #global player_search_list
    config.player_search_list = []


class CrootBot(commands.Cog, name="Croot Bot"):
    def __init__(self, bot):
        self.bot = bot

    # @commands.command(hidden=True, aliases=["cbr", ])
    # @commands.has_any_role(606301197426753536, 440639061191950336, 443805741111836693)
    # @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    # async def cb_refresh(self, ctx):
    #     """ Did HuskerBot act up? Use this only in emergencies. """
    #     await self.check_last_run(ctx)

    @commands.command(aliases=["rb", ])
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def recentballs(self, ctx, number=0):
        """ Send the last 1-5 crystal ball predictions from Steve Wiltfong. Usage is `$recent_balls [1-5]`. """
        # Error handling, Random number of 5 to prevent spam

        # This keeps bot spam down to a minimal.
        await function_helper.check_command_channel(ctx.command, ctx.channel)
        if not function_helper.correct_channel:
            await ctx.send(wrong_channel_text)
            return

        if number > 5:  # len(crystal_balls.cb_list):
            await ctx.send("The number of retrieved Crystal Balls must be less than 5.")
            return

        if not crystal_balls.cb_list:
            crystal_balls.load_cb_to_list()

        limitSpam = -1

        if number > 0:
            number -= 1

        for cbs in crystal_balls.cb_list:
            if limitSpam >= number:
                return

            varPhoto = cbs['Photo']
            varName = cbs['Name']
            varPrediction = cbs['Prediction']
            varPredictionDate = cbs['PredictionDate']
            varProfile = "[Profile]({})".format(cbs['Profile'])
            varResult = cbs['Result']
            varTeams = dict(cbs['Teams'])
            varTeamString = ""

            for x, y in varTeams.items():
                varTeamString += '{} : {}\n'.format(x, y)

            embed = discord.Embed(title="Steve Wiltfong Crystal Ball Predictions", color=0xff0000)
            embed.set_thumbnail(url=varPhoto)
            embed.add_field(name="Player Name", value=varName, inline=False)
            embed.add_field(name="Prediction", value=varPrediction, inline=True)
            embed.add_field(name="Prediction Date/Time", value=varPredictionDate, inline=True)
            embed.add_field(name="Result", value=varResult, inline=False)
            embed.add_field(name="Predicted Teams", value=varTeamString, inline=True)
            embed.add_field(name="247Sports Profile", value=varProfile, inline=False)
            embed.set_footer(text="Recent Crystal Balls" + huskerbot_footer)
            await ctx.send(embed=embed)

            limitSpam += 1

    # TODO Add error handling for `team` to be missing.
    @commands.command()
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def cb_search(self, ctx, *, team):
        """ Search through all of Steve Wiltfong's crystal ball predictions by team. """

        # This keeps bot spam down to a minimal.
        await function_helper.check_command_channel(ctx.command, ctx.channel)
        if not function_helper.correct_channel:
            await ctx.send(wrong_channel_text)
            return

        if not crystal_balls.cb_list:
            crystal_balls.load_cb_to_list()

        search_list = crystal_balls.cb_list
        saved_results = []

        for key in search_list:
            first_name = key['Name']
            prediction = key['Prediction']
            predictiondate = key['PredictionDate']
            # profile = key['Profile']
            result = key['Result']

            search_team = dict(key['Teams'])

            for x, y in search_team.items():
                if team.lower() in x.lower():
                    saved_results.append("· **{}** to [**{}**] is/was: **{}**".format(first_name, prediction, result))

        output_str = ""
        i = 1

        # Discord errors out if character limit exceeds 2,000
        for player in saved_results:
            if i > 10:
                break
            i += 1

            output_str += "{}\n".format(player)

        embed = discord.Embed(title=" ", color=0xff0000)
        embed.set_author(name="HuskerBot")
        embed.add_field(name="Crystal Ball Search Results for {}".format(team), value=output_str, inline=False)
        await ctx.send(embed=embed)

    # TODO Instead of adding a new message after clicking a search result...edit the search result message.
    @commands.command(aliases=["cb", ])
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def crootbot(self, ctx, year, *name):
        """ CrootBot provides the ability to search for and return information on football recruits. Usage is `$crootbot <year> <first_name> <last_name>`. The command is able to find partial first and last names. """
        # pulls a json file from the 247 advanced player search API and parses it to give info on the croot.
        # First, pull the message content, split the individual pieces, and make the api call

        # This keeps bot spam down to a minimal.
        await function_helper.check_command_channel(ctx.command, ctx.channel)
        if not function_helper.correct_channel:
            await ctx.send(wrong_channel_text)
            return

        if len(name) == 2:
            url = 'https://247sports.com/Season/{}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={}&Player.LastName={}'.format(year, name[0], name[1])
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
            search = requests.get(url=url, headers=headers)
            search = json.loads(search.text)
        elif len(name) == 1:
            url_first = 'https://247sports.com/Season/{}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={}'.format(year, name[0])
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
            search_first = requests.get(url=url_first, headers=headers)
            search_first = json.loads(search_first.text)

            url_last = 'https://247sports.com/Season/{}-Football/Recruits.json?&Items=15&Page=1&Player.LastName={}'.format(year, name[0])
            search_last = requests.get(url=url_last, headers=headers)
            search_last = json.loads(search_last.text)

            search = search_first + search_last
        else:
            await ctx.send("You need to provide a year and name for me to search. I accept queries in the format $crootbot <year><name>.")
            return

        if not search:
            if len(name) == 1:
                await ctx.send("I could not find any player named {} in the {} class".format(name[0], year))
            elif len(name) == 2:
                await ctx.send("I could not find any player named {} {} in the {} class".format(name[0], name[1], year))
        elif len(search) > 1:
            # global player_search_list
            # players_string='Mulitple results found for **[{}, {} {}]**. React with the corresponding emoji for CrootBot results.\n__**Search Results:**__\n'.format(year, first_name, last_name)
            players_string = ''
            players_list = []
            config.player_search_list = search
            for i in range(min(10, len(search))):
                player = search[i]['Player']
                first_name = player['FirstName']
                last_name = player['LastName']
                position = player['PrimaryPlayerPosition']['Abbreviation']
                if position in long_positions:
                    position = long_positions[position]
                players_string += '{}: {} {} - {}\n'.format(emoji_list[i], first_name, last_name, position)
                players_list.append(['FirstName', 'LastName'])

            # Embed stuff
            result_text = ''
            if len(name) == 2:
                result_text = 'Mulitple results found for __**[{}, {} {}]**__. React with the corresponding emoji for CrootBot results.\n\n'.format(year, name[0], name[1])
            elif len(name) == 1:
                result_text = 'Mulitple results found for __**[{}, {}]**__. React with the corresponding emoji for CrootBot results.\n\n'.format(year, name[0])

            embed_text = result_text + players_string
            embed = discord.Embed(title="Search Results", description=embed_text, color=0xff0000)
            embed.set_author(name="HuskerBot CrootBot")
            embed.set_footer(text='Search Results ' + huskerbot_footer)
            # await ctx.send(players_string)
            await ctx.send(embed=embed)
        else:
            channel = ctx.channel
            await parse_search(search[0], channel)  # The json that is returned is a list of dictionaries, I pull the first item in the list (may consider adding complexity)


def setup(bot):
    bot.add_cog(CrootBot(bot))
