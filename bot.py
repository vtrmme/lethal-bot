import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

# ─────────────────────────────────────────
#  CONFIG — variables de entorno
# ─────────────────────────────────────────
TOKEN    = os.environ["DISCORD_TOKEN"]
GUILD_ID = int(os.environ["DISCORD_GUILD_ID"])

# Colores
RED    = 0xC0392B
GOLD   = 0xFFD700
DARK   = 0x1a1a2e
TEAL   = 0x1ABC9C
GREEN  = 0x2ECC71

# ─────────────────────────────────────────
#  INTENTS & BOT
# ─────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot  = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ─────────────────────────────────────────
#  BASE DE DATOS
# ─────────────────────────────────────────
DB_FILE = "data.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"members": {}, "honor": {}, "applications": {}}
    db = json.load(open(DB_FILE, "r"))
    db.setdefault("applications", {})
    return db

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─────────────────────────────────────────
#  UTILIDAD — CAMBIAR NICKNAME
# ─────────────────────────────────────────
async def set_level_nick(member: discord.Member, level: int):
    base = member.display_name.split(" (LvL:")[0]
    try:
        await member.edit(nick=f"{base} (LvL: {level})")
    except discord.Forbidden:
        pass


# ═════════════════════════════════════════
#  SISTEMA DE POSTULACIÓN — MODAL
# ═════════════════════════════════════════

class ApplicationModal(discord.ui.Modal, title="⚔️  LETHAL Crew — Application"):
    level = discord.ui.TextInput(
        label="What is your current Blox Fruits level?",
        placeholder="e.g. 2400",
        min_length=1,
        max_length=4
    )
    hours = discord.ui.TextInput(
        label="How many hours do you play per week?",
        placeholder="e.g. 15",
        min_length=1,
        max_length=3
    )
    reason = discord.ui.TextInput(
        label="Why do you want to join LETHAL?",
        style=discord.TextStyle.paragraph,
        placeholder="Tell us why you want to be part of the crew...",
        min_length=20,
        max_length=500
    )
    experience = discord.ui.TextInput(
        label="Do you have experience in other crews?",
        style=discord.TextStyle.paragraph,
        placeholder="If yes, which ones and what was your rank?",
        required=False,
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        db  = load_db()
        uid = str(interaction.user.id)

        if db["applications"].get(uid, {}).get("status") == "pending":
            await interaction.response.send_message(
                "⚠️ You already have a **pending application**. Wait for staff to review it.",
                ephemeral=True
            )
            return

        db["applications"][uid] = {
            "name":       interaction.user.display_name,
            "user_id":    uid,
            "level":      self.level.value,
            "hours":      self.hours.value,
            "reason":     self.reason.value,
            "experience": self.experience.value or "None",
            "status":     "pending",
            "timestamp":  datetime.utcnow().isoformat()
        }
        save_db(db)

        # Buscar canal #join-requests
        channel = discord.utils.get(interaction.guild.text_channels, name="join-requests")
        if not channel:
            await interaction.response.send_message(
                "❌ Channel **#join-requests** not found. Ask an admin to create it.",
                ephemeral=True
            )
            return

        # Embed para los admins en #join-requests
        embed = discord.Embed(
            title="📋  New Crew Application",
            color=GOLD,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Applicant",   value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="📈 Level",        value=self.level.value,              inline=True)
        embed.add_field(name="⏱️ Hours/week",   value=self.hours.value,              inline=True)
        embed.add_field(name="❓ Why LETHAL?",  value=self.reason.value,             inline=False)
        embed.add_field(name="⚔️ Experience",   value=self.experience.value or "None", inline=False)
        embed.set_footer(text=f"User ID: {uid}  |  ⚔️ LETHAL Crew")

        view = ApplicationReviewView(uid)
        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "✅ Your application has been submitted!\nStaff will review it soon. You'll receive a DM with the result.",
            ephemeral=True
        )


# ─────────────────────────────────────────
#  BOTONES DE REVISIÓN — ACEPTAR / RECHAZAR
# ─────────────────────────────────────────

class ApplicationReviewView(discord.ui.View):
    def __init__(self, applicant_id: str):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label="✅  Accept", style=discord.ButtonStyle.success, custom_id="accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only admins can review applications.", ephemeral=True)
            return

        db  = load_db()
        uid = self.applicant_id
        app = db["applications"].get(uid)

        if not app or app["status"] != "pending":
            await interaction.response.send_message("⚠️ This application was already reviewed.", ephemeral=True)
            return

        db["applications"][uid]["status"]      = "accepted"
        db["applications"][uid]["reviewed_by"] = interaction.user.display_name
        save_db(db)

        guild  = interaction.guild
        member = guild.get_member(int(uid))
        if member:
            ronin_role    = discord.utils.get(guild.roles, name="Ronin")
            ashigaru_role = discord.utils.get(guild.roles, name="Ashigaru")
            if ronin_role:
                await member.add_roles(ronin_role)
            if ashigaru_role:
                await member.remove_roles(ashigaru_role)
            try:
                dm = discord.Embed(
                    title="⚔️  Application Accepted!",
                    description=(
                        "Congratulations, warrior.\n"
                        "Your application to **LETHAL** has been **accepted**.\n\n"
                        "You have been granted the rank of **🌊 Ronin**.\n"
                        "The full server is now unlocked for you.\n"
                        "Prove your worth and rise through the ranks.\n\n"
                        "*Honor. Loyalty. Lethal.*"
                    ),
                    color=GREEN
                )
                await member.send(embed=dm)
            except Exception:
                pass

        original_embed = interaction.message.embeds[0]
        original_embed.color = GREEN
        original_embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value=f"✅ **Accepted** by {interaction.user.mention}",
            inline=False
        )
        for child in self.children:
            child.disabled = True

        await interaction.message.edit(embed=original_embed, view=self)
        await interaction.response.send_message(
            f"✅ **{app['name']}** accepted. Role **Ronin** assigned.", ephemeral=True
        )

    @discord.ui.button(label="❌  Reject", style=discord.ButtonStyle.danger, custom_id="reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only admins can review applications.", ephemeral=True)
            return

        db  = load_db()
        uid = self.applicant_id
        app = db["applications"].get(uid)

        if not app or app["status"] != "pending":
            await interaction.response.send_message("⚠️ This application was already reviewed.", ephemeral=True)
            return

        db["applications"][uid]["status"]      = "rejected"
        db["applications"][uid]["reviewed_by"] = interaction.user.display_name
        save_db(db)

        guild  = interaction.guild
        member = guild.get_member(int(uid))
        if member:
            try:
                dm = discord.Embed(
                    title="⚔️  Application Rejected",
                    description=(
                        "Unfortunately your application to **LETHAL** has been **rejected** at this time.\n\n"
                        "Keep training and you may apply again in the future.\n\n"
                        "*Keep grinding, warrior.*"
                    ),
                    color=RED
                )
                await member.send(embed=dm)
            except Exception:
                pass

        original_embed = interaction.message.embeds[0]
        original_embed.color = RED
        original_embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value=f"❌ **Rejected** by {interaction.user.mention}",
            inline=False
        )
        for child in self.children:
            child.disabled = True

        await interaction.message.edit(embed=original_embed, view=self)
        await interaction.response.send_message(
            f"❌ **{app['name']}** rejected.", ephemeral=True
        )


# ═════════════════════════════════════════
#  EVENTOS AUTOMÁTICOS
# ═════════════════════════════════════════

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"⚔️  LETHAL BOT online como {bot.user}")

@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild

    ashigaru_role = discord.utils.get(guild.roles, name="Ashigaru")
    if ashigaru_role:
        await member.add_roles(ashigaru_role)

    channel = (discord.utils.get(guild.text_channels, name="introductions")
            or discord.utils.get(guild.text_channels, name="announcements"))

    if channel:
        embed = discord.Embed(
            title="⛩️  A new warrior arrives...",
            description=(
                f"**{member.mention}** has entered the dojo.\n\n"
                "You have been granted the rank of **🔰 Ashigaru**.\n"
                "Only crew members can access the full server.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📜 Read **#rules** before anything\n"
                "🎴 Introduce yourself in **#introductions**\n"
                "📋 Go to **#apply-here** to join the crew\n"
                "━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=RED,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits")
        await channel.send(embed=embed)

    try:
        dm = discord.Embed(
            title="⚔️  Welcome to LETHAL",
            description=(
                "You've just entered the LETHAL dojo.\n\n"
                "**To access the full server:**\n"
                "1️⃣  Read the rules in **#rules**\n"
                "2️⃣  Introduce yourself in **#introductions**\n"
                "3️⃣  Go to **#apply-here** and use `/apply`\n"
                "4️⃣  Wait for staff — you'll get a DM with the result\n\n"
                "*Honor. Loyalty. Lethal.*"
            ),
            color=GOLD
        )
        await member.send(embed=dm)
    except Exception:
        pass


# ═════════════════════════════════════════
#  /help
# ═════════════════════════════════════════

@tree.command(name="help", description="Show all LETHAL bot commands", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️  LETHAL BOT — Command Guide",
        description=(
            "All commands use `/` — type `/` in chat to autocomplete them.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=RED,
        timestamp=datetime.utcnow()
    )
    embed.add_field(
        name="✉️  Application",
        value=(
            "`/apply` — Submit your application to join LETHAL *(use in #apply-here)*\n"
            "`/application-status` — Check the status of your application\n"
            "`/delete-apply` — Delete your application to submit a new one\n"
            "`/applications` — List all pending applications *(admin only)*"
        ),
        inline=False
    )
    embed.add_field(
        name="📈  Rank & Levels",
        value=(
            "`/register-level [level]` — Register your BF level for the first time\n"
            "`/update-level [level]` — Update your level after grinding\n"
            "`/leaderboard` — Top 10 crew members by level\n"
            "`/my-stats` — View your full LETHAL profile\n\n"
            "📝 Your nickname updates automatically to `Username (LvL: X)`"
        ),
        inline=False
    )
    embed.add_field(
        name="🏆  Honor System",
        value=(
            "`/honor [@user]` — Give 1 honor point *(admin only)*\n"
            "`/my-honor` — Check your honor points & next rank\n"
            "`/honor-board` — Top 10 most honored members\n"
            "`/honor-log` — Your rank milestone progress\n\n"
            "🔓 **Auto-ranks:** `10pts` → Ronin  ·  `25pts` → Samurai  ·  `50pts` → Hatamoto *(manual)*"
        ),
        inline=False
    )
    embed.add_field(
        name="📜  Server *(admin only)*",
        value=(
            "`/setup-apply` — Post the application instructions embed in #apply-here\n"
            "`/rules` — Post the LETHAL rules embed in #rules\n"
            "`/help` — Show this command guide"
        ),
        inline=False
    )
    embed.add_field(
        name="🤖  Automatic",
        value=(
            "• Member joins → **Ashigaru role** + welcome embed + DM\n"
            "• Application accepted → **Ronin role** assigned, Ashigaru removed, DM sent\n"
            "• Application rejected → **DM sent** to applicant\n"
            "• Level registered/updated → **Nickname** updated automatically\n"
            "• Honor milestone → **Role upgrade** applied automatically"
        ),
        inline=False
    )
    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits  |  Honor. Loyalty. Lethal.")
    await interaction.response.send_message(embed=embed)


# ═════════════════════════════════════════
#  /setup-apply
# ═════════════════════════════════════════

@tree.command(name="setup-apply", description="Post the application instructions in #apply-here (admin only)", guild=discord.Object(id=GUILD_ID))
async def setup_apply(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only admins can use this command.", ephemeral=True)
        return

    channel = discord.utils.get(interaction.guild.text_channels, name="apply-here")
    if not channel:
        await interaction.response.send_message(
            "❌ Channel **#apply-here** not found. Create it first then run this command again.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="⛩️  LETHAL CREW — Join Application",
        description=(
            "Think you have what it takes to be part of **LETHAL**?\n"
            "Fill out the application below and the staff will review it.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=RED
    )
    embed.add_field(
        name="📋  What we look for",
        value=(
            "⚔️ Active players who contribute to the crew\n"
            "🌊 Team-oriented mindset — crew first, always\n"
            "🏆 Respect for all crew members and staff\n"
            "🔥 Passion for Blox Fruits and improving"
        ),
        inline=False
    )
    embed.add_field(
        name="📝  How to apply",
        value=(
            "Type `/apply` in this channel.\n"
            "A form will pop up — fill it in and submit.\n"
            "Staff will review your application and you'll receive a **DM** with the result."
        ),
        inline=False
    )
    embed.add_field(
        name="⏳  Review time",
        value="Applications are usually reviewed within **24–48 hours**.",
        inline=False
    )
    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        value="*Ready to prove yourself? Type `/apply` below.*  ⚔️",
        inline=False
    )
    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits  |  Honor. Loyalty. Lethal.")

    await channel.send(embed=embed)
    await interaction.response.send_message(
        f"✅ Application instructions posted in {channel.mention}.", ephemeral=True
    )


# ═════════════════════════════════════════
#  COMANDOS DE POSTULACIÓN
# ═════════════════════════════════════════

@tree.command(name="apply", description="Submit your application to join LETHAL Crew", guild=discord.Object(id=GUILD_ID))
async def apply(interaction: discord.Interaction):
    db  = load_db()
    uid = str(interaction.user.id)

    ronin_role = discord.utils.get(interaction.guild.roles, name="Ronin")
    if ronin_role and ronin_role in interaction.user.roles:
        await interaction.response.send_message(
            "⚠️ You are already a crew member!", ephemeral=True
        )
        return

    app = db["applications"].get(uid, {})
    if app.get("status") == "pending":
        await interaction.response.send_message(
            "⚠️ You already have a **pending application**. Wait for staff to review it.",
            ephemeral=True
        )
        return

    await interaction.response.send_modal(ApplicationModal())


@tree.command(name="application-status", description="Check the status of your application", guild=discord.Object(id=GUILD_ID))
async def application_status(interaction: discord.Interaction):
    db  = load_db()
    uid = str(interaction.user.id)
    app = db["applications"].get(uid)

    if not app:
        await interaction.response.send_message(
            "❌ You haven't submitted an application yet. Go to **#apply-here** and use `/apply`.",
            ephemeral=True
        )
        return

    status  = app["status"]
    colors  = {"pending": GOLD, "accepted": GREEN, "rejected": RED}
    icons   = {"pending": "⏳", "accepted": "✅", "rejected": "❌"}
    labels  = {"pending": "Pending review", "accepted": "Accepted", "rejected": "Rejected"}

    embed = discord.Embed(
        title="📋  Your Application Status",
        color=colors.get(status, GOLD),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="📊 Status",     value=f"{icons[status]} **{labels[status]}**", inline=True)
    embed.add_field(name="📈 Level",      value=app.get("level", "?"),                   inline=True)
    embed.add_field(name="⏱️ Hours/week", value=app.get("hours", "?"),                   inline=True)

    if status == "accepted":
        embed.add_field(name="🎉", value="Welcome to LETHAL! You are now a **Ronin**.", inline=False)
    elif status == "rejected":
        embed.add_field(name="💬", value="You may apply again in the future. Keep grinding!", inline=False)
    else:
        embed.add_field(name="⏳", value="Your application is being reviewed. Hang tight!", inline=False)

    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="delete-apply", description="Delete your application so you can submit a new one", guild=discord.Object(id=GUILD_ID))
async def delete_apply(interaction: discord.Interaction):
    db  = load_db()
    uid = str(interaction.user.id)
    app = db["applications"].get(uid)

    if not app:
        await interaction.response.send_message(
            "❌ You don't have any application to delete.",
            ephemeral=True
        )
        return

    if app.get("status") == "accepted":
        await interaction.response.send_message(
            "⚠️ Your application was **accepted** — you are already a crew member!",
            ephemeral=True
        )
        return

    del db["applications"][uid]
    save_db(db)

    embed = discord.Embed(
        title="🗑️  Application Deleted",
        description=(
            "Your application has been deleted.\n"
            "You can now submit a new one by going to **#apply-here** and using `/apply`."
        ),
        color=GOLD
    )
    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="applications", description="List all pending applications (admin only)", guild=discord.Object(id=GUILD_ID))
async def applications_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only admins can use this command.", ephemeral=True)
        return

    db      = load_db()
    pending = [(uid, a) for uid, a in db["applications"].items() if a.get("status") == "pending"]

    if not pending:
        await interaction.response.send_message("✅ No pending applications at the moment.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"📋  Pending Applications ({len(pending)})",
        color=GOLD,
        timestamp=datetime.utcnow()
    )
    for uid, a in pending:
        embed.add_field(
            name=f"👤 {a['name']}",
            value=f"📈 Level: **{a['level']}**  ·  ⏱️ **{a['hours']}h/week**\n📅 {a['timestamp'][:10]}",
            inline=False
        )
    embed.set_footer(text="Go to #join-requests to accept or reject them  |  ⚔️ LETHAL")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ═════════════════════════════════════════
#  RANK & LEVELS
# ═════════════════════════════════════════

@tree.command(name="register-level", description="Register your Blox Fruits level", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(level="Your current level in Blox Fruits (1–2800)")
async def register_level(interaction: discord.Interaction, level: int):
    if not 1 <= level <= 2800:
        await interaction.response.send_message("❌ Level must be between **1** and **2800**.", ephemeral=True)
        return
    db  = load_db()
    uid = str(interaction.user.id)
    db["members"].setdefault(uid, {})
    db["members"][uid].update({
        "level": level,
        "name":  interaction.user.display_name.split(" (LvL:")[0],
    })
    save_db(db)
    await set_level_nick(interaction.user, level)
    base = interaction.user.display_name.split(" (LvL:")[0]
    embed = discord.Embed(
        title="📈  Level Registered",
        description=(
            f"**{interaction.user.mention}** — Level **{level}** saved.\n"
            f"Nickname updated to `{base} (LvL: {level})`"
        ),
        color=GOLD
    )
    embed.set_footer(text="Use /update-level to keep it current")
    await interaction.response.send_message(embed=embed)


@tree.command(name="update-level", description="Update your current Blox Fruits level", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(level="Your new level")
async def update_level(interaction: discord.Interaction, level: int):
    if not 1 <= level <= 2800:
        await interaction.response.send_message("❌ Level must be between **1** and **2800**.", ephemeral=True)
        return
    db  = load_db()
    uid = str(interaction.user.id)
    if uid not in db["members"]:
        await interaction.response.send_message("❌ Not registered. Use `/register-level` first.", ephemeral=True)
        return
    old  = db["members"][uid].get("level", 0)
    base = interaction.user.display_name.split(" (LvL:")[0]
    db["members"][uid]["level"] = level
    db["members"][uid]["name"]  = base
    save_db(db)
    await set_level_nick(interaction.user, level)
    embed = discord.Embed(
        title="⬆️  Level Updated",
        description=(
            f"**{base}**: `{old}` → **`{level}`**\n"
            f"Nickname updated to `{base} (LvL: {level})`"
        ),
        color=GOLD
    )
    await interaction.response.send_message(embed=embed)


@tree.command(name="leaderboard", description="Top 10 LETHAL members by level", guild=discord.Object(id=GUILD_ID))
async def leaderboard(interaction: discord.Interaction):
    db = load_db()
    if not db["members"]:
        await interaction.response.send_message("No members registered yet.", ephemeral=True)
        return
    top    = sorted(db["members"].values(), key=lambda x: x.get("level", 0), reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["⚔️"] * 7
    lines  = [f"{medals[i]}  **{m['name']}** — Level `{m.get('level','?')}`" for i, m in enumerate(top)]
    embed  = discord.Embed(title="⛩️  LETHAL — Level Leaderboard", description="\n".join(lines), color=RED, timestamp=datetime.utcnow())
    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits")
    await interaction.response.send_message(embed=embed)


@tree.command(name="my-stats", description="View your full LETHAL profile", guild=discord.Object(id=GUILD_ID))
async def my_stats(interaction: discord.Interaction):
    db  = load_db()
    uid = str(interaction.user.id)
    m   = db["members"].get(uid)
    if not m:
        await interaction.response.send_message("❌ Not registered. Use `/register-level` first.", ephemeral=True)
        return
    honor = db["honor"].get(uid, 0)
    embed = discord.Embed(title=f"⚔️  {m.get('name', interaction.user.display_name)} — LETHAL Profile", color=GOLD, timestamp=datetime.utcnow())
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="📈 Level",  value=f"`{m.get('level','?')}`", inline=True)
    embed.add_field(name="🏆 Honor",  value=f"`{honor} pts`",          inline=True)
    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits")
    await interaction.response.send_message(embed=embed)


# ═════════════════════════════════════════
#  HONOR SYSTEM
# ═════════════════════════════════════════

HONOR_ROLES = {10: "Ronin", 25: "Samurai"}

async def check_honor_promotion(member: discord.Member, points: int):
    guild = member.guild
    for threshold in sorted(HONOR_ROLES.keys()):
        if points >= threshold:
            role = discord.utils.get(guild.roles, name=HONOR_ROLES[threshold])
            if role and role not in member.roles:
                await member.add_roles(role)


@tree.command(name="honor", description="Give 1 honor point to a crew member (admin only)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="The member to honor")
async def honor_cmd(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only admins can give honor.", ephemeral=True)
        return
    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ You cannot honor yourself.", ephemeral=True)
        return
    if member.bot:
        await interaction.response.send_message("❌ You cannot honor a bot.", ephemeral=True)
        return
    db  = load_db()
    uid = str(member.id)
    db["honor"].setdefault(uid, 0)
    db["honor"][uid] += 1
    pts = db["honor"][uid]
    save_db(db)
    await check_honor_promotion(member, pts)
    embed = discord.Embed(
        title="🏆  Honor Granted",
        description=f"**{interaction.user.display_name}** honored **{member.display_name}**!\nTotal: **{pts} pts**",
        color=GOLD
    )
    if pts in HONOR_ROLES:
        embed.add_field(name="🎖️ Rank Up!", value=f"**{member.display_name}** is now a **{HONOR_ROLES[pts]}**!", inline=False)
    embed.set_footer(text="50pts → Hatamoto (manual review required)")
    await interaction.response.send_message(embed=embed)


@tree.command(name="my-honor", description="Check your current honor points and next rank", guild=discord.Object(id=GUILD_ID))
async def my_honor(interaction: discord.Interaction):
    db        = load_db()
    uid       = str(interaction.user.id)
    pts       = db["honor"].get(uid, 0)
    next_rank = next(((t, r) for t, r in sorted(HONOR_ROLES.items()) if pts < t), None)
    progress  = f"\nNext rank: **{next_rank[1]}** in `{next_rank[0] - pts}` more pts" if next_rank else "\n🏅 Max auto-rank achieved! Ask a Shogun for Hatamoto."
    embed     = discord.Embed(
        title=f"🏆  {interaction.user.display_name.split(' (LvL:')[0]} — Honor Points",
        description=f"**{pts} pts**{progress}",
        color=GOLD
    )
    embed.set_footer(text="Honor is granted by admins only")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="honor-board", description="Top 10 most honored crew members", guild=discord.Object(id=GUILD_ID))
async def honor_board(interaction: discord.Interaction):
    db = load_db()
    if not db.get("honor"):
        await interaction.response.send_message("No honor points recorded yet.", ephemeral=True)
        return
    members  = db.get("members", {})
    sorted_h = sorted(db["honor"].items(), key=lambda x: x[1], reverse=True)[:10]
    medals   = ["🥇", "🥈", "🥉"] + ["⚔️"] * 7
    lines    = [f"{medals[i]}  **{members.get(uid, {}).get('name', f'User {uid}')}** — `{pts} pts`" for i, (uid, pts) in enumerate(sorted_h)]
    embed    = discord.Embed(title="🏆  LETHAL — Honor Leaderboard", description="\n".join(lines), color=GOLD, timestamp=datetime.utcnow())
    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits")
    await interaction.response.send_message(embed=embed)


@tree.command(name="honor-log", description="View your rank milestone progress", guild=discord.Object(id=GUILD_ID))
async def honor_log(interaction: discord.Interaction):
    db  = load_db()
    uid = str(interaction.user.id)
    pts = db["honor"].get(uid, 0)
    milestones = [f"{'✅' if pts >= t else '🔒'} **{t} pts** → {r}" for t, r in sorted(HONOR_ROLES.items())]
    milestones.append(f"{'✅' if pts >= 50 else '🔒'} **50 pts** → Hatamoto *(manual review)*")
    embed = discord.Embed(title=f"📜  {interaction.user.display_name.split(' (LvL:')[0]} — Honor Log", color=GOLD)
    embed.add_field(name="🏆 Current Points",  value=f"`{pts} pts`",        inline=False)
    embed.add_field(name="🎖️ Rank Milestones", value="\n".join(milestones), inline=False)
    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ═════════════════════════════════════════
#  RULES EMBED
# ═════════════════════════════════════════

@tree.command(name="rules", description="Post the official LETHAL crew rules (admin only)", guild=discord.Object(id=GUILD_ID))
async def rules_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only admins can post the rules.", ephemeral=True)
        return
    rules_channel = discord.utils.get(interaction.guild.text_channels, name="rules")
    target = rules_channel or interaction.channel
    embed = discord.Embed(
        title="⛩️  LETHAL CREW — Official Rules",
        description=(
            "These are the laws of the dojo.\n"
            "Break them and face the consequences.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=RED,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="① Respect",      value="Treat every member with respect. No harassment, insults, or discrimination of any kind.", inline=False)
    embed.add_field(name="② No Spam",      value="No spam, flooding, or excessive tagging. Keep each channel to its purpose.", inline=False)
    embed.add_field(name="③ Stay Active",  value="Inactive members for more than 2 weeks without notice may be removed from the crew.", inline=False)
    embed.add_field(name="④ Crew First",   value="Help your crew members in raids and boss fights. A strong crew beats any solo player.", inline=False)
    embed.add_field(name="⑤ No Betrayal",  value="Do not attack, steal from, or sabotage fellow LETHAL members. Betrayal = instant kick.", inline=False)
    embed.add_field(name="⑥ Fair Trading", value="All trades between members must be fair. Scamming within the crew will not be tolerated.", inline=False)
    embed.add_field(name="⑦ Follow Staff", value="Respect the decisions of Shogun, Hatamoto and Samurai at all times.", inline=False)
    embed.add_field(name="⑧ No Cheating",  value="Using hacks or exploits in Blox Fruits reflects on the whole crew. Strictly forbidden.", inline=False)
    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        value="By staying in this server you agree to all rules above.\n*Honor. Loyalty. Lethal.* ⚔️",
        inline=False
    )
    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits  |  Enforced by Staff")
    await target.send(embed=embed)
    await interaction.response.send_message(f"✅ Rules posted in {target.mention}.", ephemeral=True)


# ═════════════════════════════════════════
#  ARRANCAR EL BOT
# ═════════════════════════════════════════
bot.run(TOKEN)
