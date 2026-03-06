⚔️ LETHAL BOT — GUÍA DE DESPLIEGUE
=====================================
GitHub + Render (hosting gratuito)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 1 — PREPARAR EL BOT EN DISCORD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Ve a https://discord.com/developers/applications
2. Clic en "New Application" → ponle nombre (ej: Lethal Bot)
3. Ve a la pestaña "Bot" → clic en "Add Bot"
4. En "Privileged Gateway Intents" activa:
   ✅ SERVER MEMBERS INTENT
   ✅ MESSAGE CONTENT INTENT
5. Copia el TOKEN (lo necesitarás más adelante)

Para invitar el bot a tu servidor:
1. Ve a OAuth2 → URL Generator
2. Selecciona scopes: ✅ bot  ✅ applications.commands
3. Selecciona permisos: ✅ Manage Roles  ✅ Manage Nicknames
                        ✅ Send Messages  ✅ Embed Links
                        ✅ Read Message History
4. Copia la URL generada, ábrela y autoriza el bot

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 2 — SUBIR A GITHUB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Crea una cuenta en https://github.com si no tienes
2. Clic en "New repository"
   - Nombre: lethal-bot
   - Visibilidad: Private (importante, nunca público)
   - Clic en "Create repository"

3. Instala Git en tu PC si no lo tienes:
   https://git-scm.com/downloads

4. Abre una terminal en la carpeta del bot y ejecuta:

   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/lethal-bot.git
   git push -u origin main

   (Cambia TU_USUARIO por tu usuario de GitHub)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 3 — DESPLEGAR EN RENDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Crea una cuenta en https://render.com
   (puedes entrar con tu cuenta de GitHub)

2. Clic en "New +" → "Background Worker"

3. Conecta tu repositorio de GitHub:
   - Autoriza Render en GitHub si te lo pide
   - Selecciona el repo "lethal-bot"

4. Configura el servicio:
   - Name: lethal-bot
   - Environment: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: python bot.py

5. Añade las variables de entorno:
   Clic en "Environment" → "Add Environment Variable"

   Key: DISCORD_TOKEN
   Value: (pega aquí el token de tu bot)

   Key: DISCORD_GUILD_ID
   Value: (pega aquí el ID de tu servidor)

6. Clic en "Create Background Worker"

Render instalará las dependencias y arrancará el bot.
En los logs verás:
   ⚔️  LETHAL BOT online como Lethal Bot#1234

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTUALIZAR EL BOT EN EL FUTURO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cada vez que hagas cambios en bot.py:

   git add .
   git commit -m "Descripcion del cambio"
   git push

Render detectará el push automáticamente
y desplegará la nueva versión solo.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARCHIVOS DEL PROYECTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
bot.py           — Código principal del bot
requirements.txt — Dependencias de Python
Procfile         — Instrucciones para Render
.gitignore       — Archivos que NO se suben a GitHub
README.txt       — Esta guía

⚠️  AVISO IMPORTANTE SOBRE LOS DATOS:
El archivo data.json (base de datos) está en .gitignore
y NO se sube a GitHub. Render lo crea automáticamente
al arrancar, pero si el servicio se reinicia los datos
se borran. Para guardar los datos de forma permanente
considera usar una base de datos externa gratuita como
Supabase (https://supabase.com) o PlanetScale.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Honor. Loyalty. Lethal. ⚔️
