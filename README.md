# Discord Plays DOOM

Una implementacion interactiva y asincrona inspirada en el concepto de Twitch Plays Pokemon, que permite a una comunidad en Discord jugar al clasico DOOM (1993) de forma colaborativa mediante votacion democratica en tiempo real.

El proyecto corre el motor ViZDoom en segundo plano (headless), capturando los fotogramas de la simulacion, procesandolos como secuencias dinamicas en memoria volatil y proyectando la experiencia de juego directamente sobre la interfaz de Discord.
Caracteristicas Principales
Motor Headless en Tiempo Real: Integracion directa con ViZDoom para ejecutar la logica nativa del juego (mapa base E1M1 y progresion episodica completa).

Renderizado en Memoria (Zero Disk I/O): Generacion de secuencias animadas (GIF) directamente en buffers de RAM (io.BytesIO) utilizando Pillow y NumPy, evitando desgaste de almacenamiento secundario y minimizando la latencia.

Control de Concurrencia y Rate Limits: Ventanas de votacion calibradas de forma asincrona (asyncio) para procesar el consenso de los usuarios sin saturar la API de Discord.

UI/UX Libre de Flicker: Estrategia de entrega de archivos adjuntos directos con nombres dinamicos para eludir el sistema de cache del cliente de Discord y eliminar pantallas grises de recarga.

HUD y Progresion Automatica: Monitoreo dinamico de variables del motor (Salud, Armadura, Municion y Arma actual) y transicion automatica de mapas tras completar la salida de cada nivel.

Arquitectura
El flujo de ejecucion opera de forma desacoplada y asincrona a traves de los siguientes modulos:

Entrada de usuario (Discord Gateway): Los usuarios interactuan con la interfaz de botones expuesta mediante discord.ui.View.

Agregacion de votos: El bucle asincrono (asyncio) recolecta y pondera las acciones dentro de ventanas temporales controladas.

Ejecucion en el motor: La accion ganadora se traduce en tics discretos ejecutados por el nucleo de ViZDoom.

Captura y compresion: El buffer de pantalla RGB24 se procesa en memoria volatil (io.BytesIO) con NumPy y Pillow para generar un archivo GIF sin escribir en disco.

Actualizacion de interfaz: El mensaje original en Discord se actualiza de manera reactiva con la nueva secuencia de fotogramas y el estado del HUD.

Requisitos Previos
Python 3.10 o superior

ViZDoom y dependencias del sistema operativo (C++ build tools / CMake si se compila localmente)

Archivo de juego compatible (doom1.wad shareware o comercial)

Bot de Discord registrado con permisos para enviar mensajes, adjuntar archivos y leer contenido de mensajes

Instalacion y Configuracion
Clonar el repositorio:

Bash
git clone [https://github.com/benjaarchiles/DoomDisc.git](https://github.com/benjaarchiles/DoomDisc.git)
cd DoomDisc
Crear y activar el entorno virtual:

Bash
python -m venv venv
En Windows:

PowerShell
.\venv\Scripts\activate
En Linux / macOS:

Bash
source venv/bin/activate
Instalar dependencias:

Bash
pip install -r requirements.txt
Variables de entorno:
Crear un archivo .env en la raiz del proyecto y definir el token del bot:

Fragmento de código
DISCORD_TOKEN=tu_token_secreto_aqui
Archivo WAD:
Asegurate de que el archivo doom1.wad este ubicado en la raiz del proyecto.

Ejecucion
Inicia el servicio del bot:

Bash
python bot.py
En cualquier canal de texto donde el bot tenga permisos, ejecuta:

Plaintext
!playdoom
Licencia
Distribuido bajo la Licencia MIT. Consulta el archivo LICENSE para mas informacion.