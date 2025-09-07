const socket = io();
let peers = {}; // Clave: socket.id del otro peer, Valor: { peer: instancia de SimplePeer, username: 'nombre' }
let roomName = null;
let logEl = null;

function log(msg) {
  if (!logEl) logEl = document.getElementById('log');
  logEl.innerHTML += msg + "<br/>";
  logEl.scrollTop = logEl.scrollHeight;
}

// --- MEJORA: Función para loguear eventos con estilo ---
function logEvent(message) {
    log(`<span class="italic text-gray-500">${message}</span>`);
}


function join() {
  roomName = document.getElementById('room').value || 'default';
  socket.emit('join', { room: roomName });
  logEvent("Conectado a sala: " + roomName);
}

function leave() {
  if (roomName) {
    socket.emit('leave', { room: roomName });
    roomName = null;
  }
  for (const sid in peers) {
    if (peers[sid] && peers[sid].peer) {
      peers[sid].peer.destroy();
    }
  }
  peers = {};
  logEvent("Saliste de la sala.");
}

function createPeer(targetSid, username, initiator = false) {
  logEvent(`Creando conexión con ${username}...`);
  const peer = new SimplePeer({
    initiator,
    trickle: true,
  });

  peer.on('signal', signal => {
    socket.emit('signal', {
      target_sid: targetSid,
      signal: signal,
    });
  });

  peer.on('connect', () => {
    logEvent(`Conexión P2P establecida con ${username} ✅`);
  });

  peer.on('data', buffer => {
    handleData(buffer, targetSid);
  });
  
  peer.on('close', () => {
    logEvent(`Conexión con ${peers[targetSid]?.username || 'un usuario'} cerrada.`);
    delete peers[targetSid];
  });

  peer.on('error', err => {
    logEvent(`Error en conexión con ${peers[targetSid]?.username || 'un usuario'}: ${err.message}`);
    delete peers[targetSid];
  });

  return peer;
}

function handleData(buffer, fromSid) {
    let msg = '';
    try {
        msg = new TextDecoder().decode(buffer);
    } catch (e) {
        // No es texto
    }

    const peerState = peers[fromSid];
    if (!peerState) return;

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
            logEvent(`Archivo de ${peerState.username} recibido y descargado ✅`);
            
            delete peerState._fileMeta;
            delete peerState._fileChunks;
        } else {
            peerState._fileChunks.push(buffer);
        }
    } 
    else if (msg.startsWith("FILEMETA::")) {
        const meta = JSON.parse(msg.replace("FILEMETA::", ""));
        peerState._fileMeta = meta;
        peerState._fileChunks = [];
        logEvent(`Recibiendo archivo de ${peerState.username}: ${meta.name} (${meta.size} bytes)`);
    } else {
        log(`<strong>${peerState.username}:</strong> ${msg}`);
    }
}


// --- Lógica de Señalización de Socket.IO (Actualizada) ---

socket.on('existing_peers', existingPeers => {
  logEvent("Peers existentes en la sala: " + Object.values(existingPeers).join(', '));
  for (const sid in existingPeers) {
      const username = existingPeers[sid];
      const peer = createPeer(sid, username, true);
      peers[sid] = { peer, username };
  }
});

socket.on('peer_joined', payload => {
  const { sid, username } = payload;
  logEvent(`${username} se ha unido a la sala.`);
  const peer = createPeer(sid, username, false);
  peers[sid] = { peer, username };
});

socket.on('signal', payload => {
  const { caller_sid, signal, caller_username } = payload;
  if (peers[caller_sid]) {
    peers[caller_sid].peer.signal(signal);
  } else {
    logEvent(`Recibiendo señal de un nuevo peer ${caller_username}.`);
    const peer = createPeer(caller_sid, caller_username, false);
    peers[caller_sid] = { peer, username: caller_username };
    peers[caller_sid].peer.signal(signal);
  }
});

socket.on('peer_left', payload => {
  const { sid, username } = payload;
  logEvent(`${username} ha abandonado la sala.`);
  if (peers[sid] && peers[sid].peer) {
    peers[sid].peer.destroy();
  }
  delete peers[sid];
});


// --- Funciones para enviar datos a todos ---

function sendMsg() {
  const msg = document.getElementById('msg').value;
  if (!msg) return;
  
  log("<strong>Tú:</strong> " + msg);
  document.getElementById('msg').value = '';

  for (const sid in peers) {
    if (peers[sid] && peers[sid].peer && peers[sid].peer.connected) {
      peers[sid].peer.send(msg);
    }
  }
}

function sendFile() {
  const file = document.getElementById('fileInput').files[0];
  if (!file) {
      logEvent("Por favor, selecciona un archivo primero.");
      return;
  }

  const meta = { name: file.name, size: file.size, type: file.type };
  const metaString = "FILEMETA::" + JSON.stringify(meta);
  
  logEvent("Preparando envío de archivo a todos los peers...");

  for (const sid in peers) {
    if (peers[sid] && peers[sid].peer && peers[sid].peer.connected) {
      const peer = peers[sid].peer;
      
      ((p, s) => {
        p.send(metaString);
        const reader = file.stream().getReader();
        function pump() {
          reader.read().then(({done, value}) => {
            if (done) {
              p.send("FILEEND");
              return;
            }
            p.send(value);
            pump();
          });
        }
        pump();
      })(peer, sid);
    }
  }
  logEvent(`Archivo "${file.name}" enviado ✅`);
}
