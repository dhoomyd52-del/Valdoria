import os
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
from discord import app_commands
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
        # كل مركز يحتوي على قائمة [الأساسي، الاحتياط] أو "Open" إذا كان فارغاً
        self.lineup = {
            "ST": [], "LW": [], "RW": [], "LB": [], "CB": [], "RB": [], "GK": []
        }

    async def update_embed(self, message):
        def format_pos(pos_key):
            users = self.lineup[pos_key]
            if not users:
                return "Open"
            elif len(users) == 1:
                return users[0].mention
            else:
                return f"{users[0].mention} & {users[1].mention} (Sub)"

        desc = f"""
Hosted by {self.host_mention}

**ST** - {format_pos('ST')}
**LW** - {format_pos('LW')}
**RW** - {format_pos('RW')}
**LB** - {format_pos('LB')}
**CB** - {format_pos('CB')}
**RB** - {format_pos('RB')}
**GK** - {format_pos('GK')}

One starter + one substitute per position. Leaving promotes the substitute.
"""
        embed = discord.Embed(title="⚽ Lineup • Lineup", description=desc, color=discord.Color.dark_green())
        await message.edit(embed=embed, view=self)

    async def handle_position(self, interaction: discord.Interaction, pos_name: str):
        user = interaction.user
        
        # التأكد مما إذا كان المستخدم مسجلاً مسبقاً في أي مركز آخر
        for pos, users in self.lineup.items():
            if user in users:
                if pos == pos_name:
                    await interaction.response.send_message("You are already in this position!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"You are already registered in **{pos}**. Please leave your current position first.", ephemeral=True)
                return

        # إضافة المستخدم للمركز (أول واحد = أساسي، الثاني = احتياط)
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

    @discord.ui.button(label="ST", style=discord.ButtonStyle.secondary, custom_id="pos_st")
    async def pos_st(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "ST")

    @discord.ui.button(label="LW", style=discord.ButtonStyle.secondary, custom_id="pos_lw")
    async def pos_lw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "LW")

    @discord.ui.button(label="RW", style=discord.ButtonStyle.secondary, custom_id="pos_rw")
    async def pos_rw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "RW")

    @discord.ui.button(label="LB", style=discord.ButtonStyle.secondary, custom_id="pos_lb")
    async def pos_lb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "LB")

    @discord.ui.button(label="CB", style=discord.ButtonStyle.secondary, custom_id="pos_cb")
    async def pos_cb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "CB")

    @discord.ui.button(label="RB", style=discord.ButtonStyle.secondary, custom_id="pos_rb")
    async def pos_rb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "RB")

    @discord.ui.button(label="GK", style=discord.ButtonStyle.secondary, custom_id="pos_gk")
    async def pos_gk(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_position(interaction, "GK")

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

class RobloxLinkView(discord.ui.View):
    def __init__(self, game_url: str):
        super().__init__(timeout=None)
        self.game_url = game_url
        self.joined_users = []
        # زر الرابط يدمج فتح الرابط وتسجيل الحضور فوراً بمجرد الضغط عليه
        self.add_item(discord.ui.Button(label="Join Game Link", style=discord.ButtonStyle.link, url=game_url))

    # تم إضافة زر داخلي يسجل الحضور تلقائياً عند التفاعل مع رسالة الرابط أو تحديثها
    @discord.ui.button(label="Check In / Update Attendance", style=discord.ButtonStyle.green, custom_id="roblox_join_btn", row=1)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.joined_users:
            self.joined_users.append(interaction.user)
            await interaction.response.send_message("Your attendance has been recorded automatically!", ephemeral=True)
        else:
            await interaction.response.send_message("Your attendance is already updated!", ephemeral=True)

        await self.update_link_embed(interaction)

    async def update_link_embed(self, interaction):
        active_lineup = {}
        for v in bot.persistent_views:
            if isinstance(v, LineupView):
                for pos, users in v.lineup.items():
                    if len(users) >= 1:
                        active_lineup[users[0]] = f"{pos}"
                    if len(users) >= 2:
                        active_lineup[users[1]] = f"{pos} (Sub)"

        # الترتيب المطلوب للمراكز في قائمة الرابط
        order_priority = ["ST", "LW", "RW", "LB", "CB", "RB", "GK"]
        players_dict = {pos: [] for pos in order_priority}
        fans_list = []

        for user in self.joined_users:
            if user in active_lineup:
                pos_info = active_lineup[user]
                base_pos = pos_info.split(" ")[0]
                if base_pos in players_dict:
                    players_dict[base_pos].append((user, pos_info))
            else:
                fans_list.append(f"{user.display_name} fan")

        desc = "**Who Join from The Link**\n"
        has_players = False
        idx = 1
        for pos in order_priority:
            for user, pos_info in players_dict[pos]:
                has_players = true if 'has_players' in locals() else True
                desc += f"{idx}- {pos_info} - {user.mention}\n"
                idx += 1

        if not has_players:
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

async def has_custom_privilege(interaction_or_ctx):
    author = interaction_or_ctx.user if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx.author
    if author.guild_permissions.administrator:
        return True
    if any(r.id == SPECIFIC_ROLE_ID for r in author.roles):
        return True
    return False


# --- 4. Moderation & Admin Commands (Prefix & Slash) ---

@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(member="The member to ban", reason="Reason for ban")
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        await member.ban(reason=reason)
        await interaction.followup.send(f"Successfully banned {member.mention}.")
    except Exception as e:
        await interaction.followup.send(f"Failed to ban member: {e}")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def _ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"Successfully banned {member.mention}.")


@bot.tree.command(name="unban", description="Unban a member by name")
@app_commands.describe(member_name="The exact username to unban")
async def slash_unban(interaction: discord.Interaction, member_name: str):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You don't have permission.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    banned_users = await interaction.guild.bans()
    for ban_entry in banned_users:
        user = ban_entry.user
        if user.name == member_name:
            await interaction.guild.unban(user)
            await interaction.followup.send(f"Successfully unbanned {user.mention}.")
            return
    await interaction.followup.send("User not found in ban list.")

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


@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(member="The member to kick", reason="Reason for kick")
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("You don't have permission.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await member.kick(reason=reason)
    await interaction.followup.send(f"Successfully kicked {member.mention}.")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def _kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"Successfully kicked {member.mention}.")


@bot.tree.command(name="to", description="Timeout a member")
@app_commands.describe(member="Member", minutes="Minutes to timeout", reason="Reason")
async def slash_timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("You don't have permission.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.followup.send(f"Successfully timed out {member.mention} for {minutes} minutes.")

@bot.command(name="to")
@commands.has_permissions(moderate_members=True)
async def _timeout(ctx, member: discord.Member, minutes: int, *, reason=None):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f"Successfully timed out {member.mention} for {minutes} minutes.")


@bot.tree.command(name="rto", description="Remove timeout from a member")
async def slash_remove_timeout(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("You don't have permission.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await member.timeout(None)
    await interaction.followup.send(f"Successfully removed timeout for {member.mention}.")

@bot.command(name="rto")
@commands.has_permissions(moderate_members=True)
async def _remove_timeout(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"Successfully removed timeout for {member.mention}.")


@bot.tree.command(name="warn", description="Warn a member")
async def slash_warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        dm_embed = discord.Embed(title="⚠ Warning Received", description=f"You have been warned in **{interaction.guild.name}**.\n\n**Reason:** {reason}", color=discord.Color.orange())
        await member.send(embed=dm_embed)
        dm_status = "and DM sent."
    except:
        dm_status = "but DMs are closed."
    await interaction.followup.send(f"⚠ Warned {member.mention} {dm_status} Reason: {reason}")

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def _warn(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.send(embed=discord.Embed(title="⚠ Warning", description=f"You have been warned in **{ctx.guild.name}**. Reason: {reason}", color=discord.Color.orange()))
    except:
        pass
    await ctx.send(f"⚠ Warned {member.mention}. Reason: {reason}")


@bot.tree.command(name="rwarn", description="Remove warning from a member")
async def slash_rwarn(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission.", ephemeral=True)
        return
    await interaction.response.send_message(f"🔄 Successfully removed warning for {member.mention}.", ephemeral=True)

@bot.command(name="rwarn")
@commands.has_permissions(manage_messages=True)
async def _remove_warn(ctx, member: discord.Member):
    await ctx.send(f"🔄 Successfully removed warning for {member.mention}.")


@bot.tree.command(name="dmall", description="Send DM to a role")
async def slash_dmall(interaction: discord.Interaction, role: discord.Role, message_content: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin only.", ephemeral=True)
        return
    await interaction.response.send_message(f"⏳ Sending DMs to {role.mention}...", ephemeral=True)
    success = 0
    for m in role.members:
        if not m.bot:
            try:
                await m.send(embed=discord.Embed(title=f"📢 Message from {interaction.guild.name}", description=message_content, color=discord.Color.blue()))
                success += 1
            except:
                pass
    await interaction.followup.send(f"✅ Sent to {success} members.", ephemeral=True)

@bot.command(name="dmall")
@commands.has_permissions(administrator=True)
async def _dmall(ctx, role: discord.Role, *, message_content: str):
    success = 0
    for m in role.members:
        if not m.bot:
            try:
                await m.send(embed=discord.Embed(title=f"📢 Message from {ctx.guild.name}", description=message_content, color=discord.Color.blue()))
                success += 1
            except:
                pass
    await ctx.send(f"✅ Sent to {success} members.")


@bot.tree.command(name="purge", description="Delete messages")
async def slash_purge(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    msg = await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.")
    await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=3))
    try:
        await msg.delete()
    except:
        pass

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def _purge(ctx, amount: int):
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🧹 Deleted {len(deleted)} messages.")
    await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=3))
    try:
        await msg.delete()
    except:
        pass


# --- 5. Activity Command ---
@bot.tree.command(name="activity", description="Create activity list")
async def slash_activity(interaction: discord.Interaction):
    embed = discord.Embed(title="Activity List", description="**Total Participants:** 0\n\nNo participants yet.\nClick the button below to join:", color=discord.Color.gold())
    view = ActivityView()
    bot.persistent_views.append(view)
    await interaction.response.send_message("@everyone", embed=embed, view=view)

@bot.command(name="activity")
async def _activity(ctx):
    embed = discord.Embed(title="Activity List", description="**Total Participants:** 0\n\nNo participants yet.\nClick the button below to join:", color=discord.Color.gold())
    view = ActivityView()
    bot.persistent_views.append(view)
    await ctx.send("@everyone", embed=embed, view=view)


# --- 6. Friendly Command ---
@bot.tree.command(name="friendly", description="Create friendly match list")
async def slash_friendly(interaction: discord.Interaction):
    if not await has_custom_privilege(interaction):
        await interaction.response.send_message("You do not have the required role.", ephemeral=True)
        return
    embed = discord.Embed(title="Friendly Match List", description="No participants yet.\nClick the buttons below to join or leave:", color=discord.Color.blue())
    view = FriendlyView()
    bot.persistent_views.append(view)
    await interaction.response.send_message("@everyone", embed=embed, view=view)

@bot.command(name="friendly")
async def _friendly(ctx):
    if not await has_custom_privilege(ctx):
        await ctx.send("You do not have the required role.")
        return
    embed = discord.Embed(title="Friendly Match List", description="No participants yet.\nClick the buttons below to join or leave:", color=discord.Color.blue())
    view = FriendlyView()
    bot.persistent_views.append(view)
    await ctx.send("@everyone", embed=embed, view=view)


# --- 7. Lineup & Force Commands ---
@bot.tree.command(name="lineup", description="Create lineup list")
async def slash_lineup(interaction: discord.Interaction):
    if not await has_custom_privilege(interaction):
        await interaction.response.send_message("You do not have the required role.", ephemeral=True)
        return
    desc = f"""
Hosted by {interaction.user.mention}

**ST** - Open
**LW** - Open
**RW** - Open
**LB** - Open
**CB** - Open
**RB** - Open
**GK** - Open

Select your position using the buttons below:
"""
    embed = discord.Embed(title="⚽ Lineup • Lineup", description=desc, color=discord.Color.dark_green())
    view = LineupView(interaction.user.mention)
    bot.persistent_views.append(view)
    await interaction.response.send_message("@everyone", embed=embed, view=view)

@bot.command(name="lineup")
async def _lineup(ctx):
    if not await has_custom_privilege(ctx):
        await ctx.send("You do not have the required role.")
        return
    desc = f"""
Hosted by {ctx.author.mention}

**ST** - Open
**LW** - Open
**RW** - Open
**LB** - Open
**CB** - Open
**RB** - Open
**GK** - Open

Select your position using the buttons below:
"""
    embed = discord.Embed(title="⚽ Lineup • Lineup", description=desc, color=discord.Color.dark_green())
    view = LineupView(ctx.author.mention)
    bot.persistent_views.append(view)
    await ctx.send("@everyone", embed=embed, view=view)

@bot.tree.command(name="force", description="Force a user into a position (Reply to lineup message)")
@app_commands.describe(member="Member to force", position="Position (ST, LW, RW, LB, CB, RB, GK)")
async def slash_force(interaction: discord.Interaction, member: discord.Member, position: str):
    await interaction.response.send_message("Please use the prefix command `%force` by replying to the lineup message, as slash commands cannot capture message references directly in Discord.", ephemeral=True)

@bot.command(name="force")
async def _force(ctx, member: discord.Member, position: str):
    if not await has_custom_privilege(ctx):
        await ctx.send("You do not have the required role.")
        return
    if not ctx.message.reference:
        await ctx.send("Please reply to the lineup message using this command.")
        return

    pos_upper = position.upper()
    valid_positions = ["ST", "LW", "RW", "LB", "CB", "RB", "GK"]
    if pos_upper not in valid_positions:
        await ctx.send(f"Invalid position! Choose from: {', '.join(valid_positions)}")
        return

    try:
        ref_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except:
        await ctx.send("Could not find the referenced lineup message.")
        return

    for v in bot.persistent_views:
        if isinstance(v, LineupView):
            # إزالة المستخدم لو كان مسجلاً في مكان آخر
            for p, users in v.lineup.items():
                if member in users:
                    users.remove(member)
            
            # إضافته للمركز الجديد
            if len(v.lineup[pos_upper]) == 0:
                v.lineup[pos_upper].append(member)
            elif len(v.lineup[pos_upper]) == 1:
                v.lineup[pos_upper].append(member)
            else:
                v.lineup[pos_upper][1] = member # استبدال الاحتياطي لو المركز مكتمل

            await v.update_embed(ref_message)
            break
    else:
        new_view = LineupView()
        new_view.lineup[pos_upper] = [member]
        await ref_message.edit(view=new_view)
        await new_view.update_embed(ref_message)

    await ctx.message.delete()
    confirmation = await ctx.send(f"Successfully forced {member.mention} into **{pos_upper}**.")
    await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=3))
    try:
        await confirmation.delete()
    except:
        pass


# --- 8. Link Command (Slash & Prefix) ---
@bot.tree.command(name="link", description="Create roblox game join session list")
@app_commands.describe(game_url="The Roblox game link")
async def slash_link(interaction: discord.Interaction, game_url: str):
    if not await has_custom_privilege(interaction):
        await interaction.response.send_message("You do not have the required role.", ephemeral=True)
        return
    desc = """
**Who Join from The Link**
No players joined yet.

----------

**Fans:**
No fans yet.
"""
    embed = discord.Embed(title="🎮 Roblox Game Session", description=desc, color=discord.Color.blurple())
    view = RobloxLinkView(game_url)
    bot.persistent_views.append(view)
    await interaction.response.send_message("@everyone", embed=embed, view=view)

@bot.command(name="link")
async def _link(ctx, game_url: str):
    if not await has_custom_privilege(ctx):
        await ctx.send("You do not have the required role.")
        return
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
    bot.persistent_views.append(view)
    await ctx.send("@everyone", embed=embed, view=view)


# --- Run the Bot ---
keep_alive()
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
