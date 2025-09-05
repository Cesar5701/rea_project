const socket = io();
let peers = {}; // Clave: socket.id del otro peer, Valor: instancia de SimplePeer
let roomName = null;
let logEl = null;

function log(msg) {
  if (!logEl) logEl = document.getElementById('log');
  logEl.innerHTML += msg + "<br/>";
  logEl.scrollTop = logEl.scrollHeight;
}

function join() {
  roomName = document.getElementById('room').value || 'default';
  socket.emit('join', { room: roomName });
  log("Conectado a sala: " + roomName);
}

function leave() {
  if (roomName) {
    socket.emit('leave', { room: roomName });
    roomName = null;
  }
  // Destruir todas las conexiones P2P
  for (const sid in peers) {
    if (peers[sid]) {
      peers[sid].destroy();
    }
  }
  peers = {};
  log("Saliste de la sala");
}

function createPeer(targetSid, initiator = false) {
  log(`Creando conexión con peer: ${targetSid}`);
  const peer = new SimplePeer({
    initiator,
    trickle: true,
  });

  // Cuando tenemos una señal, la enviamos al peer específico a través del servidor
  peer.on('signal', signal => {
    socket.emit('signal', {
      target_sid: targetSid,
      signal: signal,
    });
  });

  peer.on('connect', () => {
    log(`Conexión P2P establecida con ${targetSid} ✅`);
  });

  peer.on('data', buffer => {
    handleData(buffer, targetSid);
  });
  
  peer.on('close', () => {
    log(`Conexión con ${targetSid} cerrada.`);
    delete peers[targetSid];
  });

  peer.on('error', err => {
    log(`Error en conexión con ${targetSid}: ${err.message}`);
    delete peers[targetSid];
  });

  return peer;
}

// --- Manejo de Datos (mensajes, archivos) ---

function handleData(buffer, fromSid) {
    // Primero, intenta decodificar el buffer para ver si es un mensaje de texto.
    let msg = '';
    try {
        msg = new TextDecoder().decode(buffer);
    } catch (e) {
        // Si falla la decodificación, es muy probable que sea un chunk binario.
    }

    const peerState = peers[fromSid] || {};

    // Si estamos en medio de una transferencia de archivo para este peer...
    if (peerState._fileMeta) {
        if (msg === "FILEEND") {
            const blob = new Blob(peerState._fileChunks);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = peerState._fileMeta.name;
            a.textContent = `Descargar ${peerState._fileMeta.name}`;
            a.click();
            URL.revokeObjectURL(url);
            log(`Archivo de ${fromSid} recibido y descargado ✅`);
            
            // Limpiar el estado de la transferencia
            delete peerState._fileMeta;
            delete peerState._fileChunks;
        } else {
            // Es un chunk de archivo, lo guardamos.
            peerState._fileChunks.push(buffer);
        }
    } 
    // Si no, verificamos si es el inicio de un archivo o un mensaje de texto.
    else if (msg.startsWith("FILEMETA::")) {
        const meta = JSON.parse(msg.replace("FILEMETA::", ""));
        peerState._fileMeta = meta;
        peerState._fileChunks = [];
        log(`Recibiendo archivo de ${fromSid}: ${meta.name} (${meta.size} bytes)`);
    } else {
        // Es un mensaje de texto normal.
        log(`${fromSid}: ${msg}`);
    }
}


// --- Lógica de Señalización de Socket.IO ---

socket.on('existing_peers', existingPeers => {
  log("Peers existentes en la sala: " + existingPeers.join(', '));
  existingPeers.forEach(sid => {
    peers[sid] = createPeer(sid, true); // Nosotros iniciamos la conexión
  });
});

socket.on('peer_joined', payload => {
  log(`Peer ${payload.sid} se ha unido. Creando conexión...`);
  peers[payload.sid] = createPeer(payload.sid, false);
});

socket.on('signal', payload => {
  const { caller_sid, signal } = payload;
  if (peers[caller_sid]) {
    peers[caller_sid].signal(signal);
  } else {
    log(`Recibiendo señal de un nuevo peer ${caller_sid}. Creando conexión...`);
    peers[caller_sid] = createPeer(caller_sid, false);
    peers[caller_sid].signal(signal);
  }
});

socket.on('peer_left', payload => {
  const { sid } = payload;
  log(`Peer ${sid} ha abandonado la sala.`);
  if (peers[sid]) {
    peers[sid].destroy();
    delete peers[sid];
  }
});


// --- Funciones para enviar datos a todos ---

function sendMsg() {
  const msg = document.getElementById('msg').value;
  if (!msg) return;
  
  log("Tú: " + msg);
  document.getElementById('msg').value = '';

  for (const sid in peers) {
    if (peers[sid] && peers[sid].connected) {
      peers[sid].send(msg);
    }
  }
}

function sendFile() {
  const file = document.getElementById('fileInput').files[0];
  if (!file) {
      log("Por favor, selecciona un archivo primero.");
      return;
  }

  const meta = { name: file.name, size: file.size, type: file.type };
  const metaString = "FILEMETA::" + JSON.stringify(meta);
  
  const chunkSize = 16 * 1024; // 16 KB

  log("Preparando envío de archivo a todos los peers...");

  for (const sid in peers) {
    if (peers[sid] && peers[sid].connected) {
      const peer = peers[sid];
      
      // Usamos una función autoejecutable para capturar el 'peer' correcto en cada iteración
      ((p, s) => {
        p.send(metaString); // 1. Enviar metadata

        const reader = file.stream().getReader();
        function pump() {
          reader.read().then(({done, value}) => {
            if (done) {
              p.send("FILEEND"); // 3. Enviar señal de fin
              return;
            }
            p.send(value); // 2. Enviar chunk de archivo
            pump();
          });
        }
        pump();
      })(peer, sid);
    }
  }
  log(`Archivo "${file.name}" enviado ✅`);
}

