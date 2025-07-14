from datetime import datetime
import random
import calendar
import discord
import pytz
from discord.ext import commands, tasks
import resources.constants as constants
from discord import app_commands

REQUIRED_ROLE_NAME = {1336363790744289331,1165451475980398662,774385926461194252}
REQUIRED_ROLE_NAME_ADMIN = {1336363790744289331,774385926461194252}

def has_allowed_role_premium(interaction: discord.Interaction) -> bool:
    user_role_ids = {role.id for role in interaction.user.roles}
    return bool(REQUIRED_ROLE_NAME.intersection(user_role_ids))

def has_allowed_role_premium_admin(interaction: discord.Interaction) -> bool:
    user_role_ids = {role.id for role in interaction.user.roles}
    return bool(REQUIRED_ROLE_NAME.intersection(user_role_ids))

premium_check = app_commands.check(lambda interaction: has_allowed_role_premium(interaction))
premium_check_admin = app_commands.check(lambda interaction: has_allowed_role_premium_admin(interaction))

def validate_birthday(month: int, day: int) -> bool:
    return 1 <= month <= 12 and 1 <= day <= 31

def format_birthday(month: int, day: int) -> str:
    try:
        return datetime(year=2000, month=month, day=day).strftime("%m-%d")
    except ValueError:
        return None
    
def set_user_birthday(user_id: int, username: str, birthday: str, upsert: bool = False):
    update_result = constants.USERS.update_one(
        {"_id": user_id},
        {
            "$set": {
                "name": username,
                "birthday": birthday
            }
        },
        upsert=upsert
    )
    return update_result

mongoClient = constants.mongo_connection

class MyCommands(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.birthdayCheck.start()
    
    '''@app_commands.command(name="ping-mongo", description="Ping the MongoDB client to check if it's working")
    async def ping_mongo_client(self, interaction: discord.Interaction):
        try:
            ALLOWED_USERS = [350793174970531840]
            if interaction.user.id not in ALLOWED_USERS:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
            
            mongoClient.client.admin.command('ping')
            await interaction.response.send_message("MongoDB client is working!")
        except Exception as e:
            print(e)
            await interaction.response.send_message("Failed to connect to MongoDB client.")
        return'''
    
    @app_commands.command(name="setbirthday", description="Insert your birthday into the database")
    @premium_check
    async def setbirthday(self, interaction: discord.Interaction, month: int, day: int):
        try:
            user = interaction.user

            if not validate_birthday(month, day):
                await interaction.response.send_message("Invalid date. Use a valid date format.", ephemeral=True)
                return

            user_exists = constants.USERS.find_one({"_id": user.id})
            if user_exists:
                await interaction.response.send_message("You have already set your birthday. Contact an admin to change it.", ephemeral=True)
                return

            birthday = format_birthday(month, day)
            if birthday is None:
                await interaction.response.send_message("Invalid date combination. Please enter a real date.", ephemeral=True)
                return

            set_user_birthday(user.id, user.name, birthday, upsert=True)

            month_name = calendar.month_name[month]
            await interaction.response.send_message(f"Your birthday has been set to {month_name} {day}.", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.send_message("Failed to add birthday", ephemeral=True)
        return
    
    @app_commands.command(name="birthdaylist", description="Get a list of everyone's birthdays")
    @premium_check
    async def birthdaylist(self, interaction: discord.Interaction):
        try:
            # Get all users from MongoDB
            users = list(constants.USERS.find({}))
            
            if not users:
                await interaction.response.send_message("No birthdays have been set yet.", ephemeral=True)
                return
            
            birthdayLeaderboard = []
            today = datetime.now()
            
            for user in users:
                if 'birthday' not in user:
                    continue

                name = user['name']
                birthday_date = datetime.strptime(user['birthday'], "%m-%d")
                today = datetime.now()

                next_birthday = datetime(
                    year=today.year,
                    month=birthday_date.month,
                    day=birthday_date.day
                )

                # If birthday passed this year use next year
                if next_birthday < today:
                    next_birthday = datetime(
                        year=today.year + 1,
                        month=birthday_date.month,
                        day=birthday_date.day
                )
                
                days_left = (next_birthday - today).days + 1

                month_name = calendar.month_name[birthday_date.month]

                birthdayLeaderboard.append(
                    (name, month_name, birthday_date.day, 0 if days_left == 365 else days_left)
                )
            
            birthdayLeaderboard.sort(key=lambda x: x[3], reverse=False)
            leaderboard_text = "\n".join([
                f"{i+1}. **{user}** - {month} {day} ({'Today!' if days_left == 0 else f'{days_left} days'})"
                for i, (user, month, day, days_left) in enumerate(birthdayLeaderboard)
            ])
            
            embed = discord.Embed(title="Birthdays", description=leaderboard_text, color=discord.Color.gold())
            embed.set_footer(text="Use /setbirthday to add your birthday!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(e)
            await interaction.response.send_message("Failed to retrieve birthday list.", ephemeral=True)
        return

    @app_commands.command(name="changebirthday", description="Change a user's birthday")
    @premium_check_admin
    async def change_birthday(self, interaction: discord.Interaction, user: discord.User, month: int, day: int):
        try:
            if not validate_birthday(month, day):
                await interaction.response.send_message("Invalid date. Use a valid date format.", ephemeral=True)
                return

            birthday = format_birthday(month, day)
            if birthday is None:
                await interaction.response.send_message("Invalid date combination. Please enter a real date.", ephemeral=True)
                return

            set_user_birthday(user.id, user.name, birthday, upsert=False)
            month_name = calendar.month_name[month]
            await interaction.response.send_message(f"{user.name}'s birthday has been updated to {month_name} {day}.", ephemeral=True)

        except Exception as e:
            print(e)
            await interaction.response.send_message("Failed to update birthday. Please contact Mateeyo.", ephemeral=True)

    #Tasks
    @tasks.loop(seconds=60)
    async def birthdayCheck(self):
        try:
            myServer = self.bot.get_channel(1355182499600531497) # 1376252625510727892 for testing, 1355182499600531497 for #birthdays channel
            guild = self.bot.get_guild(1157426887111483394) # 774385423039987742

            eastern = pytz.timezone('US/Eastern')
            now = datetime.now(eastern)

            if now.hour == 0 and now.minute == 0:  # 12:00 AM Eastern Time
                today_str = now.strftime("%m-%d")
                birthday_cursor = constants.USERS.find({"birthday": today_str})
                birthday_users = []

                for doc in birthday_cursor:
                    user_id = doc["_id"]
                    member = guild.get_member(user_id)
                    if member:
                        birthday_users.append(member.mention)
                    else:
                        birthday_users.append(doc.get("name", "Unknown User"))

                if birthday_users:
                    for user in birthday_users:
                        embed = discord.Embed(
                            title="🎉 Happy Birthday! 🎉",
                            description=f"Happy birthday to {user}! Here is 100 tickets for you! Have a good one!",
                            color=discord.Color.gold()
                        )
                        await myServer.send(content=' ', embed=embed)

        except Exception as e:
            print(e)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "❌ You need premium to access /setbirthday, and Admin to access /changebirthday.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(MyCommands(bot))