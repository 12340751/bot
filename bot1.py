import discord
from discord.ext import commands
import random
import datetime

TOKEN = "ТОКЕН_СЮДА"

KHL_TEAMS = [
    "Барыс",
    "Локомотив",
    "Сибирь",
    "ХК Сочи",
    "Лада",
    "Авангард",
    "Спартак"
]

MATCH_START_HOUR = 13   # 00:00 + 13 часов = 13:00
MIN_DURATION = 60       # минут
MAX_DURATION = 120      # минут

current_enemy = None
match_start = None
match_end = None
match_finished_today = False

votes_smesharovo = set()
votes_enemy = set()
match_history = []

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def now():
    return datetime.datetime.now()


def can_start_match():
    n = now()
    return n.hour >= MATCH_START_HOUR and not match_finished_today


def start_new_match():
    global current_enemy, match_start, match_end, match_finished_today

    current_enemy = random.choice(KHL_TEAMS)
    match_start = now()

    duration = random.randint(MIN_DURATION, MAX_DURATION)
    match_end = match_start + datetime.timedelta(minutes=duration)

    votes_smesharovo.clear()
    votes_enemy.clear()
    match_finished_today = False


def finish_match():
    global match_finished_today

    sm = len(votes_smesharovo)
    en = len(votes_enemy)

    if sm > en:
        winner = "Смешарово"
        loser = current_enemy
        text = "🏆 Победила **Смешарово**!"
    elif en > sm:
        winner = current_enemy
        loser = "Смешарово"
        text = f"🏆 Победила **{current_enemy}**!"
    else:
        winner = "Ничья"
        loser = "Ничья"
        text = "🤝 Ничья!"

    match_history.append({
        "date": now().strftime("%d.%m.%Y"),
        "enemy": current_enemy,
        "score": f"{sm}:{en}",
        "winner": winner,
        "loser": loser
    })

    match_finished_today = True
    return text


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Бот запущен как {bot.user}")


@bot.tree.command(name="матч", description="Текущий матч и голосование")
async def match(interaction: discord.Interaction):
    global match_start, match_end, match_finished_today

    n = now()

    # Новый день — сброс
    if match_start and n.date() != match_start.date():
        match_start = None
        match_end = None
        match_finished_today = False

    if not can_start_match():
        await interaction.response.send_message(
            "⏰ Матч будет сегодня в **13:00**\n❌ Пока матчей нет"
        )
        return

    if match_start is None:
        start_new_match()

    if n < match_end:
        remaining = int((match_end - n).total_seconds() // 60)

        embed = discord.Embed(
            title="🏒 Идёт матч",
            description=f"**Смешарово 🆚 {current_enemy}**",
            color=0x00ffcc
        )

        embed.add_field(
            name="⏳ До конца",
            value=f"{remaining} мин",
            inline=False
        )

        embed.add_field(
            name="🗳️ Голоса",
            value=(
                f"Смешарово: **{len(votes_smesharovo)}**\n"
                f"{current_enemy}: **{len(votes_enemy)}**"
            ),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=VoteView(current_enemy)
        )
        return

    # Матч закончился
    result = finish_match()

    await interaction.response.send_message(
        f"⏹️ **Матч завершён!**\n\n"
        f"Смешарово 🆚 {current_enemy}\n"
        f"📊 Счёт: **{len(votes_smesharovo)} : {len(votes_enemy)}**\n\n"
        f"{result}\n\n"
        f"❌ Матчей сегодня нет"
    )


class VoteView(discord.ui.View):
    def __init__(self, enemy):
        super().__init__(timeout=None)
        self.enemy = enemy

    @discord.ui.button(label="🏆 Смешарово", style=discord.ButtonStyle.success)
    async def vote_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in votes_smesharovo or uid in votes_enemy:
            await interaction.response.send_message("❗ Ты уже голосовал", ephemeral=True)
            return
        votes_smesharovo.add(uid)
        await interaction.response.send_message("✅ Голос принят", ephemeral=True)

    @discord.ui.button(label="⚔️ Противник", style=discord.ButtonStyle.danger)
    async def vote_e(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in votes_smesharovo or uid in votes_enemy:
            await interaction.response.send_message("❗ Ты уже голосовал", ephemeral=True)
            return
        votes_enemy.add(uid)
        await interaction.response.send_message("✅ Голос принят", ephemeral=True)


@bot.tree.command(name="результаты", description="Результаты всех матчей")
async def results(interaction: discord.Interaction):
    if not match_history:
        await interaction.response.send_message("📭 Матчей ещё не было")
        return

    text = "📊 **Результаты матчей**\n\n"
    for i, m in enumerate(match_history, 1):
        text += (
            f"**{i}. {m['date']}**\n"
            f"Смешарово 🆚 {m['enemy']}\n"
            f"Счёт: **{m['score']}**\n"
            f"🏆 Победитель: **{m['winner']}**\n\n"
        )

    await interaction.response.send_message(text)


bot.run("MTQ1NzcyODIyMTIwMTE3NDYxMA.Gbului.rNJEyLi0_f7j1MjduY80BwYTJRAoxxebXQeASo")
