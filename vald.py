import os
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
from datetime import timedelta

# --- 1. سيرفر الفلاسك للحفاظ على التشغيل 24/7 ---
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

# --- 2. إعدادات البوت ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# استخدمنا بادئة الأوامر % بناءً على طلبك
bot = commands.Bot(command_prefix="%", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready and running!")


# --- 3. أوامر الإدارة (Moderation Commands) ---

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def _ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"تم حظره بنجاح: {member.mention}")

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def _unban(ctx, *, member_name):
    banned_users = await ctx.guild.bans()
    for ban_entry in banned_users:
        user = ban_entry.user
        if user.name == member_name:
            await ctx.guild.unban(user)
            await ctx.send(f"تم إزالة الحظر عن: {user.mention}")
            return
    await ctx.send("لم يتم العثور على هذا المستخدم في قائمة الحظر.")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def _kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"تم طرد العضو: {member.mention}")

@bot.command(name="to")
@commands.has_permissions(moderate_members=True)
async def _timeout(ctx, member: discord.Member, minutes: int, *, reason=None):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f"تم إعطاء تايم أوت لـ {member.mention} لمدة {minutes} دقائق.")

@bot.command(name="rto")
@commands.has_permissions(moderate_members=True)
async def _remove_timeout(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"تم إزالة التايم أوت عن: {member.mention}")

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def _warn(ctx, member: discord.Member, *, reason="بدون سبب"):
    await ctx.send(f"⚠️ تم تحذير {member.mention} بنجاح. السبب: {reason}")

@bot.command(name="rwarn")
@commands.has_permissions(manage_messages=True)
async def _remove_warn(ctx, member: discord.Member):
    await ctx.send(f"🔄 تم إزالة التحذير عن العضو {member.mention}.")


# --- 4. أمر Activity (أول 3 ضاغطين) ---

class ActivityView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = []

    @discord.ui.button(label="React for activity", style=discord.ButtonStyle.green, custom_id="act_btn")
    async def activity_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            if len(self.participants) < 3:
                self.participants.append(interaction.user)
                await interaction.response.send_message("تم تسجيل مشاركتك بنجاح!", ephemeral=True)
            else:
                await interaction.response.send_message("عذراً، اكتمل العدد الأقصى (أول 3 أشخاص فقط).", ephemeral=True)
        else:
            await interaction.response.send_message("أنت مسجل مسبقاً!", ephemeral=True)

        # تحديث القائمة
        desc = "قائمة أسرع المشاركين:\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, user in enumerate(self.participants):
            desc += f"{medals[i]} {user.mention}\n"
        
        if not self.participants:
            desc += "لا توجد مشاركات حتى الآن."

        embed = discord.Embed(title="قائمة النشاط (Activity)", description=desc, color=discord.Color.gold())
        await interaction.message.edit(embed=embed, view=self)

@bot.command(name="activity")
async def _activity(ctx):
    embed = discord.Embed(title="قائمة النشاط (Activity)", description="اضغط على الزر أدناه للمشاركة (أول 3 يفوزون بالمراكز الأولى):", color=discord.Color.gold())
    view = ActivityView()
    await ctx.send(embed=embed, view=view)


# --- 5. أمر Friendly (تسجيل وإلغاء بالأسماء) ---

class FriendlyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = []

    @discord.ui.button(label="React for friendly", style=discord.ButtonStyle.blurple, custom_id="friend_reg")
    async def reg_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            self.participants.append(interaction.user)
            await interaction.response.send_message("تم إضافتك لقائمة الودية!", ephemeral=True)
        else:
            await interaction.response.send_message("أنت مسجل مسبقاً بالفعل.", ephemeral=True)
        await self.update_message(interaction)

    @discord.ui.button(label="Remove react", style=discord.ButtonStyle.red, custom_id="friend_rem")
    async def rem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participants:
            self.participants.remove(interaction.user)
            await interaction.response.send_message("تم إزالتك من قائمة الودية.", ephemeral=True)
        else:
            await interaction.response.send_message("أنت لست مسجلاً أساساً.", ephemeral=True)
        await self.update_message(interaction)

    async def update_message(self, interaction):
        desc = "المشاركون في المباريات الودية:\n\n"
        if self.participants:
            for user in self.participants:
                desc += f"• {user.mention}\n"
        else:
            desc += "لا يوجد مشاركون حالياً."

        embed = discord.Embed(title="قائمة الودية (Friendly)", description=desc, color=discord.Color.blue())
        await interaction.message.edit(embed=embed, view=self)

@bot.command(name="friendly")
async def _friendly(ctx):
    embed = discord.Embed(title="قائمة الودية (Friendly)", description="لا يوجد مشاركون حالياً.\nاضغط على الزر أدناه للانضمام أو المغادرة:", color=discord.Color.blue())
    view = FriendlyView()
    await ctx.send(embed=embed, view=view)


# --- 6. أمر Lineup (التشكيلة مع المراكز) ---

class LineupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.lineup = {
            "GK": "Open", "LB": "Open", "CB": "Open", "RB": "Open",
            "LW": "Open", "RW": "Open", "ST": "Open"
        }

    async def update_embed(self, interaction):
        desc = f"""
Hosted by {interaction.user.mention}

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

    @discord.ui.button(label="GK", style=discord.ButtonStyle.secondary, custom_id="pos_gk")
    async def pos_gk(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.lineup["GK"] = interaction.user.mention
        await interaction.response.send_message("تم وضعك في مركز GK", ephemeral=True)
        await self.update_embed(interaction)

    @discord.ui.button(label="LB", style=discord.ButtonStyle.secondary, custom_id="pos_lb")
    async def pos_lb(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.lineup["LB"] = interaction.user.mention
        await interaction.response.send_message("تم وضعك في مركز LB", ephemeral=True)
        await self.update_embed(interaction)

    @discord.ui.button(label="CB", style=discord.ButtonStyle.secondary, custom_id="pos_cb")
    async def pos_cb(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.lineup["CB"] = interaction.user.mention
        await interaction.response.send_message("تم وضعك في مركز CB", ephemeral=True)
        await self.update_embed(interaction)

    @discord.ui.button(label="RB", style=discord.ButtonStyle.secondary, custom_id="pos_rb")
    async def pos_rb(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.lineup["RB"] = interaction.user.mention
        await interaction.response.send_message("تم وضعك في مركز RB", ephemeral=True)
        await self.update_embed(interaction)

    @discord.ui.button(label="LW", style=discord.ButtonStyle.secondary, custom_id="pos_lw")
    async def pos_lw(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.lineup["LW"] = interaction.user.mention
        await interaction.response.send_message("تم وضعك في مركز LW", ephemeral=True)
        await self.update_embed(interaction)

    @discord.ui.button(label="RW", style=discord.ButtonStyle.secondary, custom_id="pos_rw")
    async def pos_rw(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.lineup["RW"] = interaction.user.mention
        await interaction.response.send_message("تم وضعك في مركز RW", ephemeral=True)
        await self.update_embed(interaction)

    @discord.ui.button(label="ST", style=discord.ButtonStyle.secondary, custom_id="pos_st")
    async def pos_st(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.lineup["ST"] = interaction.user.mention
        await interaction.response.send_message("تم وضعك في مركز ST", ephemeral=True)
        await self.update_embed(interaction)

@bot.command(name="lineup")
async def _lineup(ctx):
    desc = """
Hosted by Crown

**GK** - Open
**LB** - Open
**CB** - Open
**RB** - Open
**LW** - Open
**RW** - Open
**ST** - Open

اختر مركزك من الأزرار في الأسفل:
"""
    embed = discord.Embed(title="⚽ Lineup • Lineup", description=desc, color=discord.Color.dark_green())
    view = LineupView()
    await ctx.send(embed=embed, view=view)


# --- التشغيل ---
keep_alive()
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
