# 📄 Deploy iCardsMCP con PM2 – Guía Documentada

## 1️⃣ Preparación de la VPS

### Actualizar repositorios y paquetes
```bash
apt update
apt upgrade -y

```
Instalar Python completo y dependencias

```bash
apt install -y python3-full python3-dev build-essential libjpeg-dev zlib1g-dev libfreetype6-dev


```

Instalar Node.js LTS (necesario para PM2)
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt install -y nodejs

```

Verificar instalaciones

```bash
python3 --version
node -v
npm -v

```
## 2️⃣ Instalar PM2 globalmente

```bash
npm install -g pm2

```
PM2 será el process manager para mantener tu servidor Python siempre encendido.


## 3️⃣ Levantar tu servidor con PM2
Ir al directorio del proyecto
```bash
cd /root/iCardsMCP

```

Arrancar el servidor bajo PM2

```bash
pm2 start "uv run python server.py" --name icards

```

Guardar lista de procesos para reinicio automático
```bash
pm2 save

```

Configurar PM2 para iniciar automáticamente al arrancar la VPS
```bash
pm2 save

pm2 startup
# Copiar y ejecutar el comando que muestra, ejemplo:
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root
pm2 save

```


## 4️⃣ Comandos útiles PM2
|Acción	|Comando|
|-------|-------|
Ver estado de procesos	   | pm2 status
Ver logs en tiempo real    |pm2 logs icards
Reiniciar servidor	       | pm2 restart icards
Parar servidor	           | pm2 stop icards
Borrar servidor de         | PM2	pm2 delete icards
Guardar lista de procesos  |pm2 save
