import os
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
from datetime import timedelta

# --- 1. Flask server to keep bot alive 24/7 on Render ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="%", intents=intents)

# الرول المخصص لأمر friendly و lineup فقط
SPECIFIC_ROLE_ID = 1506678566991958037

def check_specific_role():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        for role in ctx.author.roles:
            if role.id == SPECIFIC_ROLE_ID:
                return True
        await ctx.send("عذراً، أنت لا تمتلك الرتبة المخصصة لاستخدام هذا الأمر.")
        return False
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready and running!")


# --- 3. Moderation Commands ---

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def _ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"Successfully banned {member.mention}.")

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def _unban(ctx, *, member_name):
    banned_users = await ctx.guild.bans()
    for ban_entry in banned_users:
        user = ban_entry.user
        if user.name == member_name:
            await ctx.guild.unban(user)
            await ctx.send(f"Successfully unbanned {user.mention}.")
            return
    await ctx.send("User not found in ban list.")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def _kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"Successfully kicked {member.mention}.")

@bot.command(name="to")
@commands.has_permissions(moderate_members=True)
async def _timeout(ctx, member: discord.Member, minutes: int, *, reason=None):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f"Successfully timed out {member.mention} for {minutes} minutes.")

@bot.command(name="rto")
@commands.has_permissions(moderate_members=True)
async def _remove_timeout(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"Successfully removed timeout for {member.mention}.")

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def _warn(ctx, member: discord.Member, *, reason="No reason provided"):
    await ctx.send(f"⚠️️ Successfully warned {member.mention}. Reason: {reason}")

@bot.command(name="rwarn")
@commands.has_permissions(manage_messages=True)
async def _remove_warn(ctx, member: discord.Member):
    await ctx.send(f"🔄 Successfully removed warning for {member.mention}.")


# --- 4. Activity Command ---

class ActivityView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = []

    @discord.ui.button(label="React for activity", style=discord.ButtonStyle.green, custom_id="act_btn")
    async def activity_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            if len(self.participants) < 3:
                self.participants.append(interaction.user)
                await interaction.response.send_message("Your participation has been recorded!", ephemeral=True)
            else:
                await interaction.response.send_message("Sorry, the maximum slots (top 3) are filled.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already registered!", ephemeral=True)

        desc = "Fastest participants list:\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, user in enumerate(self.participants):
            desc += f"{medals[i]} {user.mention}\n"
        
        if not self.participants:
            desc += "No participants yet."

        embed = discord.Embed(title="Activity List", description=desc, color=discord.Color.gold())
        await interaction.message.edit(embed=embed, view=self)

@bot.command(name="activity")
async def _activity(ctx):
    embed = discord.Embed(title="Activity List", description="Click the button below to join (Top 3 win the podium):", color=discord.Color.gold())
    view = ActivityView()
    await ctx.send("@everyone", embed=embed, view=view)


# --- 5. Friendly Command ---

class FriendlyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = []

    @discord.ui.button(label="React for friendly", style=discord.ButtonStyle.blurple, custom_id="friend_reg")
    async def reg_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            self.participants.append(interaction.user)
            await interaction.response.send_message("You have been added to the friendly list!", ephemeral=True)
        else:
            await interaction.response.send_message("You are already registered.", ephemeral=True)
        await self.update_message(interaction)

    @discord.ui.button(label="Remove react", style=discord.ButtonStyle.red, custom_id="friend_rem")
    async def rem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participants:
            self.participants.remove(interaction.user)
            await interaction.response.send_message("You have been removed from the friendly list.", ephemeral=True)
        else:
            await interaction.response.send_message("You were not registered.", ephemeral=True)
        await self.update_message(interaction)

    async def update_message(self, interaction):
        desc = "Friendly match participants:\n\n"
        if self.participants:
            for user in self.participants:
                desc += f"• {user.mention}\n"
        else:
            desc += "No participants yet."

        embed = discord.Embed(title="Friendly Match List", description=desc, color=discord.Color.blue())
        await interaction.message.edit(embed=embed, view=self)

@bot.command(name="friendly")
@check_specific_role()
async def _friendly(ctx):
    embed = discord.Embed(title="Friendly Match List", description="No participants yet.\nClick the buttons below to join or leave:", color=discord.Color.blue())
    view = FriendlyView()
    await ctx.send("@everyone", embed=embed, view=view)


# --- 6. Lineup Command (Updated: Limit 1 position per user + Leave Position button) ---

class LineupView(discord.ui.View):
    def __init__(self, host_mention):
        super().__init__(timeout=None)
        self.host_mention = host_mention
        self.lineup = {
            "GK": "Open", "LB": "Open", "CB": "Open", "RB": "Open",
            "LW": "Open", "RW": "Open", "ST": "Open"
        }

    async def update_embed(self, interaction):
        desc = f"""
Hosted by {self.host_mention}

**GK** - {self.lineup['GK']}
**LB** - {self.lineup['LB']}
**CB** - {self.lineup['CB']}
**RB** - {self.lineup['RB']}
**LW** - {self.lineup['LW']}
**RW** - {self.lineup['RW']}
**ST** - {self.lineup['ST']}

One starter + one substitute per position. Leaving promotes the substitute.
"""
        embed = discord.Embed(title="⚽ Lineup • Lineup", description=desc, color=discord.Color.dark_green())
        await interaction.message.edit(embed=embed, view=self)

    async def handle_position(self, interaction: discord.Interaction, pos_name: str):
        # التحقق مما إذا كان اللاعب مسجلاً مسبقاً في مركز آخر
        for pos, user in self.lineup.items():
            if user == interaction.user.mention:
                if pos == pos_name:
                    await interaction.response.send_message("You are already in this position!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"You are already registered in **{pos}**. Please leave your current position first using 'Leave position'.", ephemeral=True)
                return

        if self.lineup[pos_name] == "Open":
            self.lineup[pos_name] = interaction.user.mention
            await interaction.response.send_message(f"You have taken the {pos_name} position.", ephemeral=True)
            await self.update_embed(interaction)
        else:
            await interaction.response.send_message(f"Sorry, the {pos_name} position is already taken.", ephemeral=True)

    @discord.ui.button(label="GK", style=discord.ButtonStyle.secondary, custom_id="pos_gk")
    async def pos_gk(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "GK")

    @discord.ui.button(label="LB", style=discord.ButtonStyle.secondary, custom_id="pos_lb")
    async def pos_lb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "LB")

    @discord.ui.button(label="CB", style=discord.ButtonStyle.secondary, custom_id="pos_cb")
    async def pos_cb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "CB")

    @discord.ui.button(label="RB", style=discord.ButtonStyle.secondary, custom_id="pos_rb")
    async def pos_rb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "RB")

    @discord.ui.button(label="LW", style=discord.ButtonStyle.secondary, custom_id="pos_lw")
    async def pos_lw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "LW")

    @discord.ui.button(label="RW", style=discord.ButtonStyle.secondary, custom_id="pos_rw")
    async def pos_rw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "RW")

    @discord.ui.button(label="ST", style=discord.ButtonStyle.secondary, custom_id="pos_st")
    async def pos_st(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "ST")

    @discord.ui.button(label="Leave position", style=discord.ButtonStyle.danger, custom_id="pos_leave", row=2)
    async def pos_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        found = False
        for pos, user in self.lineup.items():
            if user == interaction.user.mention:
                self.lineup[pos] = "Open"
                found = True
        
        if found:
            await interaction.response.send_message("You have left your position.", ephemeral=True)
            await self.update_embed(interaction)
        else:
            await interaction.response.send_message("You are not registered in any position.", ephemeral=True)

@bot.command(name="lineup")
@check_specific_role()
async def _lineup(ctx):
    desc = f"""
Hosted by {ctx.author.mention}

**GK** - Open
**LB** - Open
**CB** - Open
**RB** - Open
**LW** - Open
**RW** - Open
**ST** - Open

Select your position using the buttons below:
"""
    embed = discord.Embed(title="⚽ Lineup • Lineup", description=desc, color=discord.Color.dark_green())
    view = LineupView(ctx.author.mention)
    await ctx.send("@everyone", embed=embed, view=view)


# --- Run the Bot ---
keep_alive()
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
