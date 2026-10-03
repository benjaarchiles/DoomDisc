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

#caarga de variables de entorno seguras
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("ERROR: No se encontró DISCORD_TOKEN en el archivo .env")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#configuración de episodios y mapas
MAPS = ["E1M1", "E1M2", "E1M3", "E1M4", "E1M5", "E1M6", "E1M7", "E1M8"]
current_map_idx = 0

#inicialización del motor ViZDoom
game = vzd.DoomGame()
game.set_doom_game_path("doom1.wad")
game.set_doom_map(MAPS[current_map_idx])
game.set_doom_skill(2)  #dficultad equilibrada no tan dificil ("Hey, not too rough")
game.set_screen_format(vzd.ScreenFormat.RGB24)
game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
game.set_window_visible(False)

#controles habilitados en el motor
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

#mapeo de botones a vectores de ViZDoom
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
VOTE_WINDOW_SECONDS = 1.5  #ritmo ágil para mayor dinamismo
deaths_count = 0

frame_counter = 0
def get_doom_gif_file(frames, total_duration_sec=1.5):
    pil_frames = []
    target_size = (512, 384)

    for f in frames:
        if f.ndim == 3 and f.shape[0] == 3:
            f = np.transpose(f, (1, 2, 0))
        img = Image.fromarray(f).resize(target_size, Image.Resampling.NEAREST)
        pil_frames.append(img)

    buffer = io.BytesIO()
    if pil_frames:
        frame_speed = 60  #22 FPS aprox para movimiento natural
        total_ms = int(total_duration_sec * 1000)
        
        #tiempo que tarda la animación en reproducirse
        anim_time = (len(pil_frames) - 1) * frame_speed
        
        #resto del tiempo del turno, se deja el último frame estático para que no salte el loop
        last_frame_pause = max(frame_speed, total_ms - anim_time)
        durations = [frame_speed] * (len(pil_frames) - 1) + [last_frame_pause]

        pil_frames[0].save(
            buffer,
            format="GIF",
            save_all=True,
            append_images=pil_frames[1:],
            duration=durations,
            loop=0
        )
    buffer.seek(0)
    return discord.File(fp=buffer, filename="doom.gif")
def build_hud_text(vote_summary):
    hp = int(game.get_game_variable(vzd.GameVariable.HEALTH))
    armor = int(game.get_game_variable(vzd.GameVariable.ARMOR))
    ammo = int(game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON_AMMO))
    weapon_id = int(game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON))
    weapon_str = WEAPON_NAMES.get(weapon_id, "Weapon")

    bars = max(0, min(10, hp // 10))
    hp_bar = f"[{'█' * bars}{'░' * (10 - bars)}]"

    return (
        f"**🎮 DISCORD PLAYS DOOM | {MAPS[current_map_idx]}**\n"
        f"❤️ **HP:** `{hp_bar}` {hp}% | 🛡️ **ARMOR:** {armor}%\n"
        f"🗡️ **WEAPON:** {weapon_str} | 🎒 **AMMO:** {ammo}\n"
        f"💀 **DEATHS:** {deaths_count} | 🗳️ {vote_summary}"
    )

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
    """Inicia la sesión interactiva comunitaria."""
    global current_votes, deaths_count, current_map_idx

    if game.is_episode_finished():
        game.new_episode()

    state = game.get_state()
    if not state:
        game.new_episode()
        state = game.get_state()
    file = get_doom_gif_file([state.screen_buffer], total_duration_sec=VOTE_WINDOW_SECONDS)
    view = DoomControls()
    hud_init = build_hud_text("Esperando votos...")
    message = await ctx.send(content=hud_init, file=file, view=view)

    while True:
        await asyncio.sleep(VOTE_WINDOW_SECONDS)

        #1 mantener en pausa si no hay interacción
        if not current_votes:
            continue

        #2 conteo de votos
        counts = {}
        for act in current_votes.values():
            counts[act] = counts.get(act, 0) + 1
        winning_action = max(counts, key=counts.get)
        vote_summary = f"**{winning_action.upper()}** ({counts[winning_action]} voto(s))"
        current_votes.clear()

        #3 ejecución y captura frame a frame
        action_vec = ACTIONS[winning_action]
        action_vec = ACTIONS[winning_action]
        if winning_action == "forward":
            tics = 20  #un paso largo y visible
        elif winning_action == "backward":
            tics = 14
        elif winning_action in ["left", "right"]:
            tics = 6  #giro no tan fuerte
        elif winning_action == "shoot":
            tics = 8  #disparo y retroceso completo
        else:
            tics = 6

        collected_frames = []
        for _ in range(tics):
            game.make_action(action_vec, 1)
            st = game.get_state()
            if st is not None:
                collected_frames.append(st.screen_buffer)
            if game.is_episode_finished():
                break

        #4 manejo de muerte y niveles
        if game.is_episode_finished():
            hp = int(game.get_game_variable(vzd.GameVariable.HEALTH))

            if hp <= 0:
                deaths_count += 1
                death_embed = discord.Embed(
                    title="💀 ¡EL CHAT FUE ELIMINADO!",
                    description=f"Total de bajas comunitarias: **{deaths_count}**\n*Reiniciando en {MAPS[current_map_idx]}...*",
                    color=discord.Color.dark_red()
                )
                await message.edit(embed=death_embed, attachments=[], view=None)
                await asyncio.sleep(3.0)

                game.set_doom_map(MAPS[current_map_idx])
                game.new_episode()
            else:
                current_map_idx += 1
                if current_map_idx < len(MAPS):
                    next_map = MAPS[current_map_idx]
                    win_embed = discord.Embed(
                        title="🏆 ¡NIVEL COMPLETADO!",
                        description=f"La comunidad alcanzó la salida.\n🚀 *Cargando mapa: {next_map}...*",
                        color=discord.Color.gold()
                    )
                    await message.edit(embed=win_embed, attachments=[], view=None)
                    await asyncio.sleep(3.5)

                    game.set_doom_map(next_map)
                    game.new_episode()
                else:
                    win_embed = discord.Embed(
                        title="👑 ¡VICTORIA TOTAL!",
                        description="¡El chat completó todos los mapas del Episodio 1!",
                        color=discord.Color.purple()
                    )
                    await message.edit(embed=win_embed, attachments=[], view=None)
                    current_map_idx = 0
                    game.set_doom_map(MAPS[0])
                    game.new_episode()

            view = DoomControls()

        state = game.get_state()
        if state is None:
            game.new_episode()
            continue

        if not collected_frames:
            collected_frames.append(state.screen_buffer)

       #5 renderizado final sin pantallazo gris
        new_file = get_doom_gif_file(collected_frames, total_duration_sec=VOTE_WINDOW_SECONDS)
        new_hud = build_hud_text(vote_summary)

        try:
         await message.edit(content=new_hud, attachments=[new_file], view=view)
        except discord.errors.HTTPException:
            pass


if __name__ == "__main__":
    bot.run(TOKEN)