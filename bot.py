import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

# ─────────────────────────────────────────
#  CONFIG — EDITA ESTOS DOS VALORES
# ─────────────────────────────────────────
TOKEN    = os.environ["DISCORD_TOKEN"]          # Token del bot
GUILD_ID = int(os.environ["DISCORD_GUILD_ID"]) # ID de tu servidor

# Colores
RED    = 0xC0392B
GOLD   = 0xFFD700
DARK   = 0x1a1a2e
TEAL   = 0x1ABC9C

# ─────────────────────────────────────────
#  INTENTS & BOT
# ─────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot  = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ─────────────────────────────────────────
#  BASE DE DATOS (archivo JSON local)
# ─────────────────────────────────────────
DB_FILE = "data.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"members": {}, "honor": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─────────────────────────────────────────
#  UTILIDAD — CAMBIAR NICKNAME
# ─────────────────────────────────────────
async def set_level_nick(member: discord.Member, level: int):
    """Cambia el nick del miembro a 'Username (LvL: X)'."""
    base = member.display_name.split(" (LvL:")[0]
    try:
        await member.edit(nick=f"{base} (LvL: {level})")
    except discord.Forbidden:
        pass  # Sin permisos (ej. el usuario es el owner del servidor)


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

    # Asignar rol Ashigaru automáticamente
    ashigaru_role = discord.utils.get(guild.roles, name="Ashigaru")
    if ashigaru_role:
        await member.add_roles(ashigaru_role)

    # Embed de bienvenida en #introductions
    channel = (discord.utils.get(guild.text_channels, name="introductions")
            or discord.utils.get(guild.text_channels, name="announcements"))

    if channel:
        embed = discord.Embed(
            title="⛩️  A new warrior arrives...",
            description=(
                f"**{member.mention}** has entered the dojo.\n\n"
                "You have been granted the rank of **🔰 Ashigaru**.\n"
                "Prove your worth to rise through the ranks of **LETHAL**.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📜 Read **#rules** before anything\n"
                "🎴 Introduce yourself in **#introductions**\n"
                "✉️ Apply to the crew in **#join-requests**\n"
                "❓ Use `/help` to see all bot commands\n"
                "━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=RED,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits")
        await channel.send(embed=embed)

    # DM de bienvenida
    try:
        dm = discord.Embed(
            title="⚔️  Welcome to LETHAL",
            description=(
                "You've just joined one of the most feared crews in Blox Fruits.\n\n"
                "**Getting started:**\n"
                "1️⃣  Read the rules in **#rules**\n"
                "2️⃣  Introduce yourself in **#introductions**\n"
                "3️⃣  Register your level with `/register-level`\n"
                "4️⃣  Apply to the crew in **#join-requests**\n"
                "5️⃣  Type `/help` to see all bot commands\n\n"
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
        name="📈  Rank & Levels",
        value=(
            "`/register-level [level]` — Register your BF level for the first time\n"
            "`/update-level [level]` — Update your level after grinding\n"
            "`/leaderboard` — Top 10 crew members by level\n"
            "`/my-stats` — View your full LETHAL profile\n\n"
            "📝 Your nickname will automatically update to `Username (LvL: X)`"
        ),
        inline=False
    )

    embed.add_field(
        name="🏆  Honor System",
        value=(
            "`/honor [@user]` — Give 1 honor point to a crew member *(admin only)*\n"
            "`/my-honor` — Check your current honor points & next rank\n"
            "`/honor-board` — Top 10 most honored members\n"
            "`/honor-log` — Your rank milestone progress\n\n"
            "🔓 **Auto-ranks:** `10pts` → Ronin  ·  `25pts` → Samurai  ·  `50pts` → Hatamoto *(manual)*"
        ),
        inline=False
    )

    embed.add_field(
        name="📜  Server",
        value=(
            "`/rules` — Post the LETHAL rules embed in #rules *(admin only)*\n"
            "`/help` — Show this command guide"
        ),
        inline=False
    )

    embed.add_field(
        name="🤖  Automatic (no command needed)",
        value=(
            "• Member joins → **Ashigaru role** assigned instantly\n"
            "• Member joins → **Welcome embed** posted in #introductions\n"
            "• Member joins → **DM guide** sent privately\n"
            "• Level registered/updated → **Nickname** updated automatically\n"
            "• Honor milestone reached → **Role upgrade** applied automatically"
        ),
        inline=False
    )

    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits  |  Honor. Loyalty. Lethal.")
    await interaction.response.send_message(embed=embed)


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

    embed = discord.Embed(
        title="📈  Level Registered",
        description=(
            f"**{interaction.user.mention}** — Level **{level}** saved.\n"
            f"Your nickname has been updated to `{interaction.user.display_name.split(' (LvL:')[0]} (LvL: {level})`"
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

    old      = db["members"][uid].get("level", 0)
    base     = interaction.user.display_name.split(" (LvL:")[0]
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

    embed = discord.Embed(
        title="⛩️  LETHAL — Level Leaderboard",
        description="\n".join(lines),
        color=RED,
        timestamp=datetime.utcnow()
    )
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

    embed = discord.Embed(
        title=f"⚔️  {m.get('name', interaction.user.display_name)} — LETHAL Profile",
        color=GOLD,
        timestamp=datetime.utcnow()
    )
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
    """Asigna rol automáticamente al alcanzar hitos de honor."""
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
        description=(
            f"**{interaction.user.display_name}** honored **{member.display_name}**!\n"
            f"Total: **{pts} pts**"
        ),
        color=GOLD
    )
    if pts in HONOR_ROLES:
        embed.add_field(
            name="🎖️ Rank Up!",
            value=f"**{member.display_name}** is now a **{HONOR_ROLES[pts]}**!",
            inline=False
        )
    embed.set_footer(text="50pts → Hatamoto (manual review required)")
    await interaction.response.send_message(embed=embed)


@tree.command(name="my-honor", description="Check your current honor points and next rank", guild=discord.Object(id=GUILD_ID))
async def my_honor(interaction: discord.Interaction):
    db        = load_db()
    uid       = str(interaction.user.id)
    pts       = db["honor"].get(uid, 0)
    next_rank = next(((t, r) for t, r in sorted(HONOR_ROLES.items()) if pts < t), None)
    progress  = f"\nNext rank: **{next_rank[1]}** in `{next_rank[0] - pts}` more pts" if next_rank else "\n🏅 Max auto-rank achieved! Ask a Shogun for Hatamoto."

    embed = discord.Embed(
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
    lines    = [
        f"{medals[i]}  **{members.get(uid, {}).get('name', f'User {uid}')}** — `{pts} pts`"
        for i, (uid, pts) in enumerate(sorted_h)
    ]

    embed = discord.Embed(
        title="🏆  LETHAL — Honor Leaderboard",
        description="\n".join(lines),
        color=GOLD,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="⚔️ LETHAL Crew • Blox Fruits")
    await interaction.response.send_message(embed=embed)


@tree.command(name="honor-log", description="View your rank milestone progress", guild=discord.Object(id=GUILD_ID))
async def honor_log(interaction: discord.Interaction):
    db  = load_db()
    uid = str(interaction.user.id)
    pts = db["honor"].get(uid, 0)

    milestones = [f"{'✅' if pts >= t else '🔒'} **{t} pts** → {r}" for t, r in sorted(HONOR_ROLES.items())]
    milestones.append(f"{'✅' if pts >= 50 else '🔒'} **50 pts** → Hatamoto *(manual review)*")

    embed = discord.Embed(
        title=f"📜  {interaction.user.display_name.split(' (LvL:')[0]} — Honor Log",
        color=GOLD
    )
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
