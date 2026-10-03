# Discord Plays DOOM

Una implementación interactiva y asíncrona inspirada en el concepto de Twitch Plays Pokémon, que permite a una comunidad en Discord jugar al clásico DOOM (1993) de forma colaborativa mediante votación democrática en tiempo real.

El proyecto corre el motor ViZDoom en segundo plano (headless), capturando los fotogramas de la simulación, procesándolos como secuencias dinámicas en memoria volátil y proyectando la experiencia de juego directamente sobre la interfaz de Discord.
Características Principales
Motor Headless en Tiempo Real: Integración directa con ViZDoom para ejecutar la lógica nativa del juego (mapa base E1M1 y progresión episódica completa).

Renderizado en Memoria (Zero Disk I/O): Generación de secuencias animadas (GIF) directamente en buffers de RAM (io.BytesIO) utilizando Pillow y NumPy, evitando desgaste de almacenamiento secundario y minimizando la latencia.

Control de Concurrencia y Rate Limits: Ventanas de votación calibradas de forma asíncrona (asyncio) para procesar el consenso de los usuarios sin saturar la API de Discord.

UI/UX Libre de Flicker: Estrategia de entrega de archivos adjuntos directos con nombres dinámicos para eludir el sistema de caché del cliente de Discord y eliminar pantallas grises de recarga.

HUD y Progresión Automática: Monitoreo dinámico de variables del motor (Salud, Armadura, Munición y Arma actual) y transición automática de mapas tras completar la salida de cada nivel.

## Arquitectura

El flujo de ejecución opera de forma desacoplada y asíncrona a través de los siguientes módulos:

1. **Entrada de usuario (Discord Gateway):** Los usuarios interactúan con la interfaz de botones expuesta mediante `discord.ui.View`.
2. **Agregación de votos:** El bucle asíncrono (`asyncio`) recolecta y pondera las acciones dentro de ventanas temporales controladas.
3. **Ejecución en el motor:** La acción ganadora se traduce en tics discretos ejecutados por el núcleo de **ViZDoom**.
4. **Captura y compresión:** El buffer de pantalla RGB24 se procesa en memoria volátil (`io.BytesIO`) con **NumPy** y **Pillow** para generar un archivo GIF sin escribir en disco.
5. **Actualización de interfaz:** El mensaje original en Discord se actualiza de manera reactiva con la nueva secuencia de fotogramas y el estado del HUD.

## Requisitos Previos

* Python 3.10 o superior
* ViZDoom y dependencias del sistema operativo
* Archivo de juego compatible (`doom1.wad`)
* Bot de Discord registrado y configurado

Instalación y Configuración
Clonar el repositorio:

Bash
git clone [https://github.com/benjaarchiles/DoomDisc.git](https://github.com/benjaarchiles/DoomDisc.git)
cd DoomDisc
Crear y activar el entorno virtual:

Bash
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux / macOS:
source venv/bin/activate
Instalar dependencias:

Bash
pip install -r requirements.txt
Variables de entorno: copia el archivo de ejemplo y añade el token del bot:

Bash
cp .env.example .env
Dentro de .env:

Fragmento de código
DISCORD_TOKEN=tu_token_secreto_aqui
Colocar el archivo WAD:
Asegúrate de que el archivo doom1.wad esté en la raíz del proyecto.

Ejecución
Inicia el servicio del bot:

Bash
python bot.py
En cualquier canal de texto donde el bot tenga permisos, ejecuta:

Plaintext
!playdoom
Usa los botones interactivos para votar colectivamente la dirección, los giros, disparos e interacciones con el entorno.

Licencia
Distribuido bajo la Licencia MIT. Consulta el archivo LICENSE para más información.