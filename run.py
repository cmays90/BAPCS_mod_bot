import discord
from discord.ext import commands, tasks
from discord.utils import get
import asyncio
import asyncpraw, os, requests, json, datetime
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", filemode='a', level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s')

logger.info("Starting app")
    
loop = asyncio.get_event_loop()
logger.info("Async Loop created")

bot = commands.Bot(command_prefix='!', description="BAPCS Discord Poster", loop=loop)
logger.info("Discord bot initialized")

queue = asyncio.Queue()
logger.info("Queue created")

class Submission(object):
    def __init__(self, title, url, domain, thumbnail, author, sid, flair):
        self.title = title
        self.url = url
        self.domain = domain
        self.thumbnail = thumbnail
        self.author = author
        self.sid = sid
        self.flair = flair
        logger.info("New submission created %s", sid)


@bot.event
async def on_ready():
    logger.info('Logged in as %s ||| %s', bot.user.name, bot.user.id)
    reddit_poster.start()
    loop.create_task(get_flairs())
    #get_flairs.start()


@bot.command(name='role', pass_context=True)
async def role(ctx, command="", *, value=""):
    channel = bot.get_channel(int(os.getenv("DISCORD_CHANNEL")))
    if(str(ctx.channel.id) not in os.getenv("DISCORD_ROLES_CHANNEL")) :
        return
    server_roles = channel.guild.roles
    if(command in ["help", ""]) :
        await ctx.send(f"{ctx.author.mention}, this command can add or remove roles for {channel.mention} channel alerts. Adding a role means you will be pinged anytime a new post with that flair is made on the sub.\n\nAvailable commands:\n\n!role list\n> List all available roles\n\n!role add {{role1}} {{role2}} {{role3}}\n> Add roles to your user to be alerted.  Note you do not need to include the \"alert:\" at the start of the role, and you can add as many roles as you want. Eligible to add roles will begin with \"alert:\"\n\n!role remove {{role1}} {{role2}} {{role3}}\n> Remove roles from your user and no longer be pinged about posts for that role.\n\n\nThe alert:bapcs role is special and will be pinged for every new post.  You must explicitly opt into this notification.")
    elif(command == "list"):
        roles = []
        for role in server_roles:
            if(role.name.startswith("alert:") and role.name != f"alert:{os.getenv('REDDIT_ROLENAME')}" and role.name[6::] not in roles):
                roles.append(role.name[6::])
        roles.sort()
        await ctx.send(f"{ctx.author.mention}, the following roles are available:\n> __{os.getenv('REDDIT_ROLENAME')}__ {' '.join(roles)}\n\nThe {os.getenv('REDDIT_ROLENAME')} role is special and will be pinged on every post.")
    elif(command == "add"):
        adds = value.split(" ")
        good_roles = []
        bad_roles = []
        roles = []
        for role in adds:
            logger.info(f"Adding {role} to {ctx.author.name}")
            if(not role.startswith("alert:")):
                role = f"alert:{role}"
            drole = get(server_roles, name=role)
            if(drole == None):
                bad_roles.append(role[6::])
            else:
                good_roles.append(role[6::])
                roles.append(drole)
        await ctx.author.add_roles(*roles)
        msg = f"{ctx.author.mention},\n"
        if(len(good_roles) > 0):
            msg += f"You have been added to {', '.join(good_roles)}.\n"
        if(len(bad_roles) > 0):
            msg += f"I was unable to add you to {', '.join(bad_roles)}. Please make sure these are valid roles.\n"
        await ctx.send(msg)
    elif(command == "remove"):
        dels = value.split(" ")
        good_roles = []
        bad_roles = []
        roles = []
        for role in dels:
            logger.info(f"Removing {role} from {ctx.author.name}")
            if(not role.startswith("alert:")):
                role = f"alert:{role}"
            drole = get(server_roles, name=role)
            if(drole == None):
                bad_roles.append(role[6::])
            else:
                good_roles.append(role[6::])
                roles.append(drole)
        await ctx.author.remove_roles(*roles)
        msg = f"{ctx.author.mention},\n"
        if(len(good_roles) > 0):
            msg += f"You have been removed from {', '.join(good_roles)}.\n"
        if(len(bad_roles) > 0):
            msg += f"I was unable to remove you from {', '.join(bad_roles)}. Please make sure these are valid roles.\n"
        await ctx.send(msg)
    #await ctx.send(value)
    #logger.info("Echoed %s", value)
    
@tasks.loop(seconds=1.0)
async def reddit_poster():
    logger.info("Running reddit poster on discord")
    channel = bot.get_channel(int(os.getenv("DISCORD_CHANNEL"))) # channel ID goes here
    exception = 0
    role = get(channel.guild.roles, name=f'alert:{os.getenv("REDDIT_ROLENAME")}')
    while True:
        try:
            submission = await queue.get()
            logger.info('Discord to post new messasge')
            e = discord.Embed(title=str(submission.title), url=str(submission.url))
            e.set_author(name=str(submission.domain), url="https://" + submission.domain, icon_url="https://" + str(submission.domain) +"/favicon.ico")
            if(str(submission.thumbnail) != "default"):
                e.set_image(url=str(submission.thumbnail))
            e.add_field(name="Author", value=str(submission.author), inline=True)
            e.add_field(name="Comments", value="https://redd.it/" + str(submission.sid), inline=True)
            flair_role = get(channel.guild.roles, name=f"alert:{submission.flair}")
            exception = 0
            msg = f'**{submission.title}**\n{role.mention}'
            if(flair_role != None) :
                msg = f'**{submission.title}**\n{flair_role.mention} {role.mention}'
            resp = await channel.send(msg, embed=e )
            logger.info('Posted {0.title}'.format(submission))
        except:
            
            logger.exception("Fatal error in reddit_poster loop", exc_info=True)
            exception += 1


reddit = asyncpraw.Reddit(client_id=os.getenv("REDDIT_CLIENT_ID"),
                  client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                  user_agent="BAPCS Discord Poster/v1.0",
                  username=os.getenv("REDDIT_USERNAME"),
                  password=os.getenv("REDDIT_PASSWORD"),
                  loop = loop)
logger.info("Reddit instance created")

async def reddit_submissions():
    logger.info("Reddit stream started")
    subreddit = await reddit.subreddit(os.getenv("REDDIT_SUBREDDIT"))
    exception = 0
    sleep = 1
    while True:
        try:
            async for submission in subreddit.stream.submissions(skip_existing=True):
                logger.info("New submission: " + str(submission.title))
                sub = Submission(str(submission.title), str(submission.url), str(submission.domain), str(submission.thumbnail), str(submission.author), str(submission.id), str(submission.link_flair_css_class).lower())
                await queue.put(sub)
                exception = 0
                before = ""
                #await msg.publish()  ## TODO: Figure out an alternate method for other servers to benefit from this.
        except:
            logger.exception("Fatal error in reddit_submissions loop", exc_info=True)
            exception += 1
        logger.info("Relooping for some reason")
        if(exception > 3):
            await asynio.sleep(sleep)
            sleep *= 2
            if(sleep > 60):
                sleep = 60
    logger.info("Dunno why, reddit stream ended")

async def create_role(name):
    channel = bot.get_channel(int(os.getenv("DISCORD_CHANNEL")))
    role = get(channel.guild.roles, name=f"alert:{name}")
    if(role == None):
        logger.info("Creating new role: alert:%s", name)
        new_role = await channel.guild.create_role(name=f"alert:{name}", reason="Created by Bot to sync with sub")
        logger.info("Role created: %s",str(new_role))

async def get_flairs():
    while True:
        try:
            logger.info("Getting flairs")
            subreddit = await reddit.subreddit(os.getenv("REDDIT_SUBREDDIT"))
            async for template in subreddit.flair.link_templates:
                await create_role(template['css_class'].lower())
            await create_role(os.getenv("REDDIT_ROLENAME"))
        except:
            logger.exception("Fatal error in get_flairs loop", exc_info=True)
        logger.info("Done with flair sync")
        await asyncio.sleep(3600)

loop.create_task(reddit_submissions())
loop.create_task(bot.start(os.getenv("DISCORD_TOKEN")))
logger.info("loops added")
loop.run_forever()
