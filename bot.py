import asyncio
import io
import os
import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
from PIL import Image
import numpy as np
import vizdoom as vzd

#se cargan variables de entorno de forma segura
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("ERROR: No se encontró DISCORD_TOKEN en el archivo .env")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#1 mapas de Doom 1
MAPS = ["E1M1", "E1M2", "E1M3", "E1M4", "E1M5", "E1M6", "E1M7", "E1M8"]
current_map_idx = 0

game = vzd.DoomGame()
game.set_doom_game_path("doom1.wad")
game.set_doom_map(MAPS[current_map_idx])
game.set_doom_skill(2)  # dificultad equilibrada para que no sea tan dificil("Hey, not too rough")
game.set_screen_format(vzd.ScreenFormat.RGB24)
game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
game.set_window_visible(False)

#controles habilitados
game.clear_available_buttons()
game.add_available_button(vzd.Button.MOVE_FORWARD)
game.add_available_button(vzd.Button.MOVE_BACKWARD)
game.add_available_button(vzd.Button.TURN_LEFT)
game.add_available_button(vzd.Button.TURN_RIGHT)
game.add_available_button(vzd.Button.ATTACK)
game.add_available_button(vzd.Button.USE)
game.add_available_button(vzd.Button.SELECT_NEXT_WEAPON)

#variables de estado para el HUD
game.add_available_game_variable(vzd.GameVariable.HEALTH)
game.add_available_game_variable(vzd.GameVariable.ARMOR)
game.add_available_game_variable(vzd.GameVariable.SELECTED_WEAPON_AMMO)
game.add_available_game_variable(vzd.GameVariable.SELECTED_WEAPON)

game.init()
game.new_episode()

#mapeo de acciones
ACTIONS = {
    "forward":  [1, 0, 0, 0, 0, 0, 0],
    "backward": [0, 1, 0, 0, 0, 0, 0],
    "left":     [0, 0, 1, 0, 0, 0, 0],
    "right":    [0, 0, 0, 1, 0, 0, 0],
    "shoot":    [0, 0, 0, 0, 1, 0, 0],
    "use":      [0, 0, 0, 0, 0, 1, 0],
    "weapon":   [0, 0, 0, 0, 0, 0, 1]
}

WEAPON_NAMES = {
    1: "Fist 👊",
    2: "Pistol 🔫",
    3: "Shotgun 💥",
    4: "Chaingun ⚙️",
    5: "Rocket Launcher 🚀",
    6: "Plasma Rifle ⚡",
    7: "BFG 9000 🟢",
    8: "Chainsaw 🪚"
}

current_votes = {}
VOTE_WINDOW_SECONDS = 2.0
deaths_count = 0


def get_doom_image_file(screen_buffer):
    """Convierte el frame a un discord.File directamente en memoria RAM."""
    if screen_buffer.ndim == 3 and screen_buffer.shape[0] == 3:
        screen_buffer = np.transpose(screen_buffer, (1, 2, 0))

    img = Image.fromarray(screen_buffer)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="doom_frame.png")


def build_hud_text(vote_summary):
    hp = int(game.get_game_variable(vzd.GameVariable.HEALTH))
    armor = int(game.get_game_variable(vzd.GameVariable.ARMOR))
    ammo = int(game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON_AMMO))
    weapon_id = int(game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON))
    weapon_str = WEAPON_NAMES.get(weapon_id, "Weapon")

    bars = max(0, min(10, hp // 10))
    hp_bar = f"[{'█' * bars}{'░' * (10 - bars)}]"

    hud = (
        f"**🎮 DISCORD PLAYS DOOM | MAP: {MAPS[current_map_idx]}**\n"
        f"❤️ **HP:** {hp_bar} {hp}% | 🛡️ **ARMOR:** {armor}%\n"
        f"🗡️ **WEAPON:** {weapon_str} | 🎒 **AMMO:** {ammo}\n"
        f"💀 **DEATHS:** {deaths_count} | 🗳️ {vote_summary}"
    )
    return hud


class DoomControls(View):
    def __init__(self):
        super().__init__(timeout=None)

    #fila 0: movimiento principal y combate
    @discord.ui.button(emoji="⬆️", style=discord.ButtonStyle.primary, row=0)
    async def forward(self, interaction: discord.Interaction, button: Button):
        current_votes[interaction.user.id] = "forward"
        await interaction.response.defer()

    @discord.ui.button(emoji="🔫", style=discord.ButtonStyle.danger, row=0)
    async def shoot(self, interaction: discord.Interaction, button: Button):
        current_votes[interaction.user.id] = "shoot"
        await interaction.response.defer()

    @discord.ui.button(emoji="🚪", style=discord.ButtonStyle.success, row=0)
    async def use(self, interaction: discord.Interaction, button: Button):
        current_votes[interaction.user.id] = "use"
        await interaction.response.defer()

    #fila 1: giros, retroceso y cambio de arma
    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary, row=1)
    async def turn_left(self, interaction: discord.Interaction, button: Button):
        current_votes[interaction.user.id] = "left"
        await interaction.response.defer()

    @discord.ui.button(emoji="⬇️", style=discord.ButtonStyle.primary, row=1)
    async def backward(self, interaction: discord.Interaction, button: Button):
        current_votes[interaction.user.id] = "backward"
        await interaction.response.defer()

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary, row=1)
    async def turn_right(self, interaction: discord.Interaction, button: Button):
        current_votes[interaction.user.id] = "right"
        await interaction.response.defer()

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.secondary, row=1)
    async def change_weapon(self, interaction: discord.Interaction, button: Button):
        current_votes[interaction.user.id] = "weapon"
        await interaction.response.defer()


@bot.event
async def on_ready():
    print(f" DoomBot conectado exitosamente como {bot.user}")


@bot.command()
async def playdoom(ctx):
    """Inicia la partida comunitaria"""
    global current_votes, deaths_count, current_map_idx

    if game.is_episode_finished():
        game.new_episode()

    state = game.get_state()
    if not state:
        game.new_episode()
        state = game.get_state()

    file = get_doom_image_file(state.screen_buffer)
    view = DoomControls()

    hud_init = build_hud_text("Waiting for votes...")
    message = await ctx.send(content=hud_init, file=file, view=view)

    while True:
        await asyncio.sleep(VOTE_WINDOW_SECONDS)

        #1 congelar juego si nadie vota
        if not current_votes:
            continue

        #2 conteo de votos democrático
        counts = {}
        for act in current_votes.values():
            counts[act] = counts.get(act, 0) + 1
        winning_action = max(counts, key=counts.get)
        vote_summary = f"Won: **{winning_action.upper()}** ({counts[winning_action]} vote(s))"
        current_votes.clear()

        #3 ejecución calibrada
        action_vec = ACTIONS[winning_action]
        if winning_action == "forward":
            game.make_action(action_vec, 14)
        elif winning_action == "backward":
            game.make_action(action_vec, 10)
        elif winning_action in ["left", "right"]:
            game.make_action(action_vec, 8)
        elif winning_action == "shoot":
            game.make_action(action_vec, 6)
        else:
            game.make_action(action_vec, 4)

        #4 manejo de fin de mapa o muerte
        if game.is_episode_finished():
            hp = int(game.get_game_variable(vzd.GameVariable.HEALTH))

            if hp <= 0:
                deaths_count += 1
                death_msg = (
                    f"💀 **CHAT DIED!**\n"
                    f"Total community deaths: **{deaths_count}**\n"
                    f"*Respawning at {MAPS[current_map_idx]}...*"
                )
                await message.edit(content=death_msg, view=None)
                await asyncio.sleep(3.5)

                game.set_doom_map(MAPS[current_map_idx])
                game.new_episode()
            else:
                current_map_idx += 1
                if current_map_idx < len(MAPS):
                    next_map = MAPS[current_map_idx]
                    win_msg = (
                        f"🏆 **LEVEL CLEARED!**\n"
                        f"The chat reached the exit!\n"
                        f"🚀 *Loading next map: {next_map}...*"
                    )
                    await message.edit(content=win_msg, view=None)
                    await asyncio.sleep(4.0)

                    game.set_doom_map(next_map)
                    game.new_episode()
                else:
                    win_msg = "👑 **CAMPAIGN VICTORY!**\nThe chat beat all Episode 1 maps!"
                    await message.edit(content=win_msg, view=None)
                    current_map_idx = 0
                    game.set_doom_map(MAPS[0])
                    game.new_episode()

            view = DoomControls()

        state = game.get_state()
        if state is None:
            game.new_episode()
            continue

        #5 renderizado y actualización en Discord
        new_file = get_doom_image_file(state.screen_buffer)
        new_hud = build_hud_text(vote_summary)

        try:
            await message.edit(content=new_hud, attachments=[new_file], view=view)
        except discord.errors.HTTPException:
            pass


if __name__ == "__main__":
    bot.run(TOKEN)