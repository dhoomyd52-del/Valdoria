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

# --- 2. Persistent Views ---
class ActivityView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = []

    @discord.ui.button(label="React for activity", style=discord.ButtonStyle.green, custom_id="act_btn")
    async def activity_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            self.participants.append(interaction.user)
            await interaction.response.send_message("Your participation has been recorded!", ephemeral=True)
        else:
            await interaction.response.send_message("You are already registered!", ephemeral=True)

        desc = f"**Total Participants:** {len(self.participants)}\n\nParticipants list:\n"
        if self.participants:
            for i, user in enumerate(self.participants, 1):
                desc += f"{i}. {user.mention}\n"
        else:
            desc += "No participants yet."

        embed = discord.Embed(title="Activity List", description=desc, color=discord.Color.gold())
        await interaction.message.edit(embed=embed, view=self)

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

class LineupView(discord.ui.View):
    def __init__(self, host_mention="Server Host"):
        super().__init__(timeout=None)
        self.host_mention = host_mention
        self.lineup = {
            "GK": "Open", "LB": "Open", "CB": "Open", "RB": "Open",
            "LW": "Open", "RW": "Open", "ST": "Open"
        }

    async def update_embed(self, message):
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
        await message.edit(embed=embed, view=self)

    async def handle_position(self, interaction: discord.Interaction, pos_name: str):
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
            await self.update_embed(interaction.message)
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
            await self.update_embed(interaction.message)
        else:
            await interaction.response.send_message("You are not registered in any position.", ephemeral=True)

# نظام زر رابط روبلوكس والقائمة المطلوبة
class RobloxLinkView(discord.ui.View):
    def __init__(self, game_url: str):
        super().__init__(timeout=None)
        self.game_url = game_url
        self.joined_users = [] # قائمة تخزين الأشخاص الذين ضغطوا على الزر
        # إضافة زر الانتقال للرابط خارجيًا
        self.add_item(discord.ui.Button(label="Join Game Link", style=discord.ButtonStyle.link, url=game_url))

    @discord.ui.button(label="I Have Joined / Click Here", style=discord.ButtonStyle.green, custom_id="roblox_join_btn", row=1)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.joined_users:
            self.joined_users.append(interaction.user)
            await interaction.response.send_message("Your attendance has been recorded successfully!", ephemeral=True)
        else:
            await interaction.response.send_message("You have already registered your attendance!", ephemeral=True)

        await self.update_link_embed(interaction)

    async def update_link_embed(self, interaction):
        # البحث عن التشكيلة النشطة لمعرفة المراكز في نفس الروم إن وجدت
        active_lineup = {}
        for v in bot.persistent_views:
            if isinstance(v, LineupView):
                for pos, user_mention in v.lineup.items():
                    if user_mention != "Open":
                        active_lineup[user_mention] = pos

        players_list = []
        fans_list = []

        for user in self.joined_users:
            if user.mention in active_lineup:
                pos = active_lineup[user.mention]
                players_list.append(f"{pos} - {user.mention}")
            else:
                fans_list.append(f"{user.display_name} fan")

        desc = "**Who Join from The Link**\n"
        if players_list:
            for idx, p in enumerate(players_list, 1):
                desc += f"{idx}- {p}\n"
        else:
            desc += "No players joined yet.\n"

        desc += "\n----------\n\n**Fans:**\n"
        if fans_list:
            for f in fans_list:
                desc += f"{f}\n"
        else:
            desc += "No fans yet."

        embed = discord.Embed(title="🎮 Roblox Game Session", description=desc, color=discord.Color.blurple())
        await interaction.message.edit(embed=embed, view=self)

# --- 3. Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        self.add_view(ActivityView())
        self.add_view(FriendlyView())
        self.add_view(LineupView())
        print("Persistent views added successfully.")

bot = MyBot(command_prefix="%", intents=intents)

SPECIFIC_ROLE_ID = 1506678566991958037

def check_specific_role():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        for role in ctx.author.roles:
            if role.id == SPECIFIC_ROLE_ID:
                return True
        await ctx.send("Sorry, you do not have the required role to use this command.")
        return False
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready and running!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        target_channel = None
        for guild in bot.guilds:
            channel = discord.utils.get(guild.text_channels, name="bot-messages")
            if channel:
                target_channel = channel
                break
        
        if target_channel:
            embed = discord.Embed(
                title="📩 New Direct Message Received",
                description=message.content,
                color=discord.Color.purple()
            )
            embed.set_author(name=f"{message.author} (ID: {message.author.id})", icon_url=message.author.display_avatar.url)
            await target_channel.send(embed=embed)

    await bot.process_commands(message)


# --- 4. Moderation & Admin Commands ---

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
    try:
        dm_embed = discord.Embed(
            title="⚠ Warning Received",
            description=f"You have been warned in **{ctx.guild.name}**.\n\n**Reason:** {reason}",
            color=discord.Color.orange()
        )
        await member.send(embed=dm_embed)
        dm_status = "and DM sent successfully."
    except discord.Forbidden:
        dm_status = "but could not send DM (DMs are closed)."

    await ctx.send(f"⚠ Successfully warned {member.mention} {dm_status} Reason: {reason}")

@bot.command(name="rwarn")
@commands.has_permissions(manage_messages=True)
async def _remove_warn(ctx, member: discord.Member):
    await ctx.send(f"🔄 Successfully removed warning for {member.mention}.")

@bot.command(name="dmall")
@commands.has_permissions(administrator=True)
async def _dmall(ctx, role: discord.Role, *, message_content: str):
    success_count = 0
    fail_count = 0

    status_msg = await ctx.send(f"⏳ Sending direct messages to members with role {role.mention}...")

    for member in role.members:
        if member.bot:
            continue
        try:
            embed = discord.Embed(
                title=f"📢 Message from {ctx.guild.name}",
                description=message_content,
                color=discord.Color.blue()
            )
            await member.send(embed=embed)
            success_count += 1
        except Exception:
            fail_count += 1

    await status_msg.edit(content=f"✅ Done! Successfully sent to **{success_count}** members. (Failed: {fail_count})")

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def _purge(ctx, amount: int):
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🧹 Successfully deleted {len(deleted)} messages.")
    await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=3))
    try:
        await msg.delete()
    except:
        pass


# --- 5. Activity Command ---
@bot.command(name="activity")
async def _activity(ctx):
    embed = discord.Embed(title="Activity List", description="**Total Participants:** 0\n\nNo participants yet.\nClick the button below to join:", color=discord.Color.gold())
    view = ActivityView()
    await ctx.send("@everyone", embed=embed, view=view)


# --- 6. Friendly Command ---
@bot.command(name="friendly")
@check_specific_role()
async def _friendly(ctx):
    embed = discord.Embed(title="Friendly Match List", description="No participants yet.\nClick the buttons below to join or leave:", color=discord.Color.blue())
    view = FriendlyView()
    await ctx.send("@everyone", embed=embed, view=view)


# --- 7. Lineup & Force Commands ---
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
    # نسجل الـ view في bot.persistent_views لكي يتمكن أمر الـ link من قراءتها
    bot.persistent_views.append(view)
    await ctx.send("@everyone", embed=embed, view=view)

@bot.command(name="force")
@check_specific_role()
async def _force(ctx, member: discord.Member, position: str):
    if not ctx.message.reference:
        await ctx.send("Please reply to the lineup message using this command.")
        return

    pos_upper = position.upper()
    valid_positions = ["GK", "LB", "CB", "RB", "LW", "RW", "ST"]
    if pos_upper not in valid_positions:
        await ctx.send(f"Invalid position! Choose from: {', '.join(valid_positions)}")
        return

    try:
        ref_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except:
        await ctx.send("Could not find the referenced lineup message.")
        return

    embed = ref_message.embeds[0]
    desc = embed.description

    lines = desc.split("\n")
    new_lines = []
    for line in lines:
        if line.startswith(f"**{pos_upper}**"):
            new_lines.append(f"**{pos_upper}** - {member.mention}")
        else:
            new_lines.append(line)
    
    new_desc = "\n".join(new_lines)
    updated_embed = discord.Embed(title=embed.title, description=new_desc, color=embed.color)
    
    for v in bot.persistent_views:
        if isinstance(v, LineupView):
            v.lineup[pos_upper] = member.mention
            await ref_message.edit(embed=updated_embed, view=v)
            break
    else:
        new_view = LineupView()
        new_view.lineup[pos_upper] = member.mention
        await ref_message.edit(embed=updated_embed, view=new_view)

    await ctx.message.delete()
    confirmation = await ctx.send(f"Successfully forced {member.mention} into **{pos_upper}**.")
    await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=3))
    try:
        await confirmation.delete()
    except:
        pass


# --- 8. Link Command (جديد) ---
@bot.command(name="link")
@check_specific_role()
async def _link(ctx, game_url: str):
    await ctx.message.delete()
    desc = """
**Who Join from The Link**
No players joined yet.

----------

**Fans:**
No fans yet.
"""
    embed = discord.Embed(title="🎮 Roblox Game Session", description=desc, color=discord.Color.blurple())
    view = RobloxLinkView(game_url)
    await ctx.send("@everyone", embed=embed, view=view)


# --- Run the Bot ---
keep_alive()
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
