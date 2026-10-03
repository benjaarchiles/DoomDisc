# Discord Plays DOOM

Una implementación interactiva y asíncrona inspirada en el fenómeno *Twitch Plays Pokémon*, que permite a una comunidad en Discord jugar al clásico **DOOM (1993)** de forma colaborativa mediante votación democrática en tiempo real.

El proyecto corre el motor **ViZDoom** en segundo plano (headless), capturando los fotogramas de la simulación, procesándolos como secuencias dinámicas en memoria volátil y proyectando la experiencia de juego directamente sobre la interfaz de Discord.

# Caracteristicas Principales
Motor Headless en Tiempo Real: Integración directa con ViZDoom para ejecutar la lógica nativa del juego (mapa base E1M1 y progresión episódica completa).

Renderizado en Memoria (Zero Disk I/O): Generación de secuencias animadas (GIF) directamente en buffers de RAM (io.BytesIO) utilizando Pillow y NumPy, evitando desgaste de almacenamiento secundario y minimizando la latencia.

Control de Concurrencia y Rate Limits: Ventanas de votación calibradas de forma asíncrona (asyncio) para procesar el consenso de los usuarios sin saturar la API de Discord.

UI/UX Libre de Flicker: Estrategia de entrega de archivos adjuntos directos con nombres dinámicos para eludir el sistema de caché del cliente de Discord y eliminar pantallas grises de recarga.

HUD y Progresión Automática: Monitoreo dinámico de variables del motor (Salud, Armadura, Munición y Arma actual) y transición automática de mapas tras completar la salida de cada nivel.

# Arquitectura 

[ Discord Users ]
       │
       ▼ (Interacciones de botones)
[ Discord Gateway / View (discord.py) ]
       │
       ▼ (Agregación de votos por ventana temporal)
[ Bucle de Eventos Asíncrono (asyncio) ]
       │
       ▼ (Ejecución de tics de acción)
[ Motor ViZDoom (C++ Core / Python API) ]
       │
       ▼ (Buffer de pantalla RGB24)
[ Procesamiento de Frames (NumPy & Pillow en RAM) ]
       │
       ▼ (Compresión de GIF en io.BytesIO)
[ Actualización de Mensaje en Discord (message.edit) ]

# Requisitos previos

python 3.10 o superior

ViZDoom y dependencias del sistema operativo (C++ build tools / CMake si se compila localmente)

Archivo de juego compatible (doom1.wad shareware o comercial)

Bot de Discord registrado con permisos para enviar mensajes, adjuntar archivos y leer contenido de mensajes

# Instalación y configuración

1. Clonar el repositorio:
    git clone https://github.com/benjaarchiles/DoomDisc.git
    cd DoomDisc

2. Crear y activar el entorno virtual:
    python -m venv venv
    #En Windows:
        .\venv\Scripts\activate
    #En Linux / macOS:
        source venv/bin/activate

3. Instalar dependencias:
    pip install -r requirements.txt

4. Variables de entorno: copia el archivo de ejemplo y añade el token de tu bot de discord
    cp .env.example .env
    DENTRO DE .env
    DISCORD_TOKEN =tu_token_secreto_aqui

5. Colocar el archivo WAD
    Asegúrate que el archivo doom1.wad esté en la raiz del proyecto.

# Ejecución

Inicia el servicio del bot:
    python bot.py

En cualquier canal de texto que el bot tenga permisos, ejecuta:
    !playdoom
Usa los botones interactivos para votar colectivamente la dirección, los giros, disparos e interacciones con el entorno.

# Licencia 
Distribuido bajo la Licencia MIT. Consulta el archivo LICENSE para más información.
