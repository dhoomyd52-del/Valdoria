import os
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

# --- 1. Flask server to keep bot alive ---
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

# --- 2. Persistent Views & Data ---
warnings_db = {} # {user_id: [reasons]}

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

class RobloxQueueView(discord.ui.View):
    def __init__(self, game_url: str):
        super().__init__(timeout=None)
        self.game_url = game_url
        self.add_item(discord.ui.Button(label="Join Game Link", style=discord.ButtonStyle.link, url=game_url))

class PutLinkModal(discord.ui.Modal, title="Set Roblox Game Link"):
    link_input = discord.ui.TextInput(
        label="Roblox Game Link",
        placeholder="https://www.roblox.com/games/...",
        style=discord.TextStyle.short,
        required=True
    )

    def __init__(self, lineup_view):
        super().__init__()
        self.lineup_view = lineup_view

    async def on_submit(self, interaction: discord.Interaction):
        self.lineup_view.game_url = self.link_input.value
        await interaction.response.send_message(f"✅ Game link has been updated successfully by {interaction.user.mention}!", ephemeral=True)

class LineupView(discord.ui.View):
    def __init__(self, host_mention="Server Host"):
        super().__init__(timeout=None)
        self.host_mention = host_mention
        self.game_url = "https://www.roblox.com"
        self.lineup = {
            "GK": [], "LB": [], "CB": [], "RB": [], "LW": [], "RW": [], "ST": []
        }

    async def update_embed(self, message):
        def format_pos(pos_key):
            users = self.lineup[pos_key]
            if not users:
                return "Open"
            elif len(users) == 1:
                return f"{users[0].mention}"
            else:
                return f"{users[0].mention} · Sub {users[1].mention}"

        desc = f"""
Hosted by {self.host_mention}

**GK** - {format_pos('GK')}
**LB** - {format_pos('LB')}
**CB** - {format_pos('CB')}
**RB** - {format_pos('RB')}
**LW** - {format_pos('LW')}
**RW** - {format_pos('RW')}
**ST** - {format_pos('ST')}

One starter + one substitute per position. Leaving promotes the substitute.

Note: Your click is registered immediately.
"""
        embed = discord.Embed(title="⚽ Lineup • Lineup", description=desc, color=discord.Color.dark_green())
        await message.edit(embed=embed, view=self)

    async def handle_position(self, interaction: discord.Interaction, pos_name: str):
        user = interaction.user
        
        for pos, users in self.lineup.items():
            if user in users:
                if pos == pos_name:
                    await interaction.response.send_message("You are already in this position!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"You are already registered in **{pos}**. Please leave your current position first.", ephemeral=True)
                return

        if len(self.lineup[pos_name]) == 0:
            self.lineup[pos_name].append(user)
            await interaction.response.send_message(f"You have taken the {pos_name} position as a starter.", ephemeral=True)
            await self.update_embed(interaction.message)
        elif len(self.lineup[pos_name]) == 1:
            self.lineup[pos_name].append(user)
            await interaction.response.send_message(f"You have taken the {pos_name} position as a substitute (Sub).", ephemeral=True)
            await self.update_embed(interaction.message)
        else:
            await interaction.response.send_message(f"Sorry, the {pos_name} position and its substitute slot are already full.", ephemeral=True)

    @discord.ui.button(label="GK", style=discord.ButtonStyle.secondary, custom_id="pos_gk", row=0)
    async def pos_gk(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "GK")

    @discord.ui.button(label="LB", style=discord.ButtonStyle.secondary, custom_id="pos_lb", row=0)
    async def pos_lb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "LB")

    @discord.ui.button(label="CB", style=discord.ButtonStyle.secondary, custom_id="pos_cb", row=0)
    async def pos_cb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "CB")

    @discord.ui.button(label="RB", style=discord.ButtonStyle.secondary, custom_id="pos_rb", row=0)
    async def pos_rb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "RB")

    @discord.ui.button(label="LW", style=discord.ButtonStyle.secondary, custom_id="pos_lw", row=0)
    async def pos_lw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "LW")

    @discord.ui.button(label="RW", style=discord.ButtonStyle.secondary, custom_id="pos_rw", row=1)
    async def pos_rw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "RW")

    @discord.ui.button(label="ST", style=discord.ButtonStyle.secondary, custom_id="pos_st", row=1)
    async def pos_st(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "ST")

    @discord.ui.button(label="Leave position", style=discord.ButtonStyle.danger, custom_id="pos_leave", row=2)
    async def pos_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        found = False
        for pos, users in self.lineup.items():
            if user in users:
                users.remove(user)
                found = True
        
        if found:
            await interaction.response.send_message("You have left your position.", ephemeral=True)
            await self.update_embed(interaction.message)
        else:
            await interaction.response.send_message("You are not registered in any position.", ephemeral=True)

    @discord.ui.button(label="Clear board", style=discord.ButtonStyle.danger, custom_id="pos_clear", row=2)
    async def pos_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        for pos in self.lineup:
            self.lineup[pos].clear()
        await interaction.response.send_message("🧹 Board has been cleared!", ephemeral=True)
        await self.update_embed(interaction.message)

    @discord.ui.button(label="Put Link", style=discord.ButtonStyle.secondary, custom_id="put_link", row=3)
    async def put_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PutLinkModal(self))

    @discord.ui.button(label="Get Friendly Link", style=discord.ButtonStyle.success, custom_id="get_friendly_link", row=3)
    async def get_friendly_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        order_priority = ["GK", "LB", "CB", "RB", "LW", "RW", "ST"]
        
        desc = f"**Match host:** {self.host_mention}\n**Link put by:** {interaction.user.mention}\n\n"
        
        idx = 1
        has_players = False
        for pos in order_priority:
            users = self.lineup[pos]
            if len(users) >= 1:
                has_players = True
                desc += f"{idx}. {users[0].display_name} ({users[0].mention}) · {pos} · Starter\n"
                idx += 1
            if len(users) >= 2:
                has_players = True
                desc += f"{idx}. {users[1].display_name} ({users[1].mention}) · {pos} · Sub\n"
                idx += 1

        if not has_players:
            desc += "No players confirmed yet.\n"

        desc += f"\n{idx-1 if has_players else 0} players confirmed and received the private friendly link.\nPositions update automatically from the live lineup."

        embed = discord.Embed(title="STM Queue", description=desc, color=discord.Color.blurple())
        view = RobloxQueueView(self.game_url)
        await interaction.response.send_message(embed=embed, view=view)

# --- 3. Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=["%", "?"], intents=intents)

    async def setup_hook(self):
        self.add_view(ActivityView())
        self.add_view(FriendlyView())
        self.add_view(LineupView())
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands.")
        except Exception as e:
            print(e)
        print("Persistent views added successfully.")

bot = MyBot()

SPECIFIC_ROLE_ID = 1506678566991958037

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

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

async def has_custom_privilege(interaction_or_ctx):
    author = interaction_or_ctx.user if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx.author
    if author.guild_permissions.administrator:
        return True
    if any(r.id == SPECIFIC_ROLE_ID for r in author.roles):
        return True
    return False

# --- 4. Moderation & Admin Commands ---

# Ban & Unban & Banlist
@bot.tree.command(name="ban", description="Ban a member")
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"Banned {member.mention}.")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def _ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"Banned {member.mention}.")

@bot.tree.command(name="unban", description="Unban a user by ID")
async def slash_unban(interaction: discord.Identifier if False else discord.Interaction, user_id: str, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=reason)
        await interaction.response.send_message(f"Unbanned {user.mention}.")
    except Exception as e:
        await interaction.response.send_message(f"Failed to unban: {e}", ephemeral=True)

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def _unban(ctx, user_id: str, *, reason=None):
    try:
        user = await bot.fetch_user(int(user_id))
        await ctx.guild.unban(user, reason=reason)
        await ctx.send(f"Unbanned {user.mention}.")
    except Exception as e:
        await ctx.send(f"Failed to unban: {e}")

@bot.tree.command(name="banlist", description="Show banned users list")
async def slash_banlist(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    bans = [entry async for entry in interaction.guild.bans(limit=20)]
    if not bans:
        await interaction.response.send_message("No banned users.", ephemeral=True)
        return
    desc = "\n".join([f"• {b.user} (ID: {b.user.id})" for b in bans])
    embed = discord.Embed(title="Ban List", description=desc, color=discord.Color.red())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="banlist")
@commands.has_permissions(ban_members=True)
async def _banlist(ctx):
    bans = [entry async for entry in ctx.guild.bans(limit=20)]
    if not bans:
        await ctx.send("No banned users.")
        return
    desc = "\n".join([f"• {b.user} (ID: {b.user.id})" for b in bans])
    embed = discord.Embed(title="Ban List", description=desc, color=discord.Color.red())
    await ctx.send(embed=embed)

# Kick
@bot.tree.command(name="kick", description="Kick a member")
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"Kicked {member.mention}.")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def _kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"Kicked {member.mention}.")

# Timeout (To & Rto)
@bot.tree.command(name="to", description="Timeout a member")
async def slash_timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    await interaction.response.send_message(f"Timed out {member.mention} for {minutes} minutes.")

@bot.command(name="to")
@commands.has_permissions(moderate_members=True)
async def _timeout(ctx, member: discord.Member, minutes: int, *, reason=None):
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    await ctx.send(f"Timed out {member.mention} for {minutes} minutes.")

@bot.tree.command(name="rto", description="Remove timeout from a member")
async def slash_rto(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    await member.timeout(None, reason=reason)
    await interaction.response.send_message(f"Removed timeout from {member.mention}.")

@bot.command(name="rto")
@commands.has_permissions(moderate_members=True)
async def _rto(ctx, member: discord.Member, *, reason=None):
    await member.timeout(None, reason=reason)
    await ctx.send(f"Removed timeout from {member.mention}.")

# Warnings (Warn, Rwarn, Warnlist)
@bot.tree.command(name="warn", description="Warn a member")
async def slash_warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    if member.id not in warnings_db:
        warnings_db[member.id] = []
    warnings_db[member.id].append(reason)
    try:
        await member.send(f"Warning in {interaction.guild.name}: {reason}")
    except:
        pass
    await interaction.response.send_message(f"Warned {member.mention}. Total warnings: {len(warnings_db[member.id])}")

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def _warn(ctx, member: discord.Member, *, reason="No reason provided"):
    if member.id not in warnings_db:
        warnings_db[member.id] = []
    warnings_db[member.id].append(reason)
    try:
        await member.send(f"Warning in {ctx.guild.name}: {reason}")
    except:
        pass
    await ctx.send(f"Warned {member.mention}. Total warnings: {len(warnings_db[member.id])}")

@bot.tree.command(name="rwarn", description="Remove a warning from a member")
async def slash_rwarn(interaction: discord.Interaction, member: discord.Member, index: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    if member.id in warnings_db and warnings_db[member.id]:
        if 1 <= index <= len(warnings_db[member.id]):
            removed = warnings_db[member.id].pop(index - 1)
            await interaction.response.send_message(f"Removed warning for {member.mention}: `{removed}`")
        else:
            await interaction.response.send_message("Invalid warning index number.", ephemeral=True)
    else:
        await interaction.response.send_message("This member has no warnings.", ephemeral=True)

@bot.command(name="rwarn")
@commands.has_permissions(manage_messages=True)
async def _rwarn(ctx, member: discord.Member, index: int):
    if member.id in warnings_db and warnings_db[member.id]:
        if 1 <= index <= len(warnings_db[member.id]):
            removed = warnings_db[member.id].pop(index - 1)
            await ctx.send(f"Removed warning for {member.mention}: `{removed}`")
        else:
            await ctx.send("Invalid warning index number.")
    else:
        await ctx.send("This member has no warnings.")

@bot.tree.command(name="warnlist", description="Show member's warnings")
async def slash_warnlist(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    if member.id in warnings_db and warnings_db[member.id]:
        desc = "\n".join([f"{i+1}. {r}" for i, r in enumerate(warnings_db[member.id])])
    else:
        desc = "No warnings found."
    embed = discord.Embed(title=f"Warnings for {member}", description=desc, color=discord.Color.orange())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="warnlist")
@commands.has_permissions(manage_messages=True)
async def _warnlist(ctx, member: discord.Member):
    if member.id in warnings_db and warnings_db[member.id]:
        desc = "\n".join([f"{i+1}. {r}" for i, r in enumerate(warnings_db[member.id])])
    else:
        desc = "No warnings found."
    embed = discord.Embed(title=f"Warnings for {member}", description=desc, color=discord.Color.orange())
    await ctx.send(embed=embed)

# Purge
@bot.tree.command(name="purge", description="Delete messages")
async def slash_purge(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def _purge(ctx, amount: int):
    await ctx.message.delete()
    await ctx.channel.purge(limit=amount)

# --- 5. Activity & Friendly & Lineup Commands ---
@bot.tree.command(name="activity", description="Create activity list")
async def slash_activity(interaction: discord.Interaction):
    embed = discord.Embed(title="Activity List", description="**Total Participants:** 0\n\nNo participants yet.", color=discord.Color.gold())
    view = ActivityView()
    bot.persistent_views.append(view)
    await interaction.response.send_message("@everyone", embed=embed, view=view)

@bot.command(name="activity")
async def _activity(ctx):
    embed = discord.Embed(title="Activity List", description="**Total Participants:** 0\n\nNo participants yet.", color=discord.Color.gold())
    view = ActivityView()
    bot.persistent_views.append(view)
    await ctx.send("@everyone", embed=embed, view=view)

@bot.tree.command(name="friendly", description="Create friendly match list")
async def slash_friendly(interaction: discord.Interaction):
    if not await has_custom_privilege(interaction):
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    embed = discord.Embed(title="Friendly Match List", description="No participants yet.", color=discord.Color.blue())
    view = FriendlyView()
    bot.persistent_views.append(view)
    await interaction.response.send_message("@everyone", embed=embed, view=view)

@bot.command(name="friendly")
async def _friendly(ctx):
    if not await has_custom_privilege(ctx):
        await ctx.send("No permission.")
        return
    embed = discord.Embed(title="Friendly Match List", description="No participants yet.", color=discord.Color.blue())
    view = FriendlyView()
    bot.persistent_views.append(view)
    await ctx.send("@everyone", embed=embed, view=view)

@bot.tree.command(name="lineup", description="Create lineup list")
async def slash_lineup(interaction: discord.Interaction):
    if not await has_custom_privilege(interaction):
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    desc = f"""
Hosted by {interaction.user.mention}

**GK** - Open
**LB** - Open
**CB** - Open
**RB** - Open
**LW** - Open
**RW** - Open
**ST** - Open

One starter + one substitute per position. Leaving promotes the substitute.

Note: Your click is registered immediately.
"""
    embed = discord.Embed(title="⚽ Lineup • Lineup", description=desc, color=discord.Color.dark_green())
    view = LineupView(interaction.user.mention)
    bot.persistent_views.append(view)
    await interaction.response.send_message("@everyone", embed=embed, view=view)

@bot.command(name="lineup")
async def _lineup(ctx):
    if not await has_custom_privilege(ctx):
        await ctx.send("No permission.")
        return
    desc = f"""
Hosted by {ctx.author.mention}

**GK** - Open
**LB** - Open
**CB** - Open
**RB** - Open
**LW** - Open
**RW** - Open
**ST** - Open

One starter + one substitute per position. Leaving promotes the substitute.

Note: Your click is registered immediately.
"""
    embed = discord.Embed(title="⚽ Lineup • Lineup", description=desc, color=discord.Color.dark_green())
    view = LineupView(ctx.author.mention)
    bot.persistent_views.append(view)
    await ctx.send("@everyone", embed=embed, view=view)

# --- Run Bot ---
keep_alive()
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
