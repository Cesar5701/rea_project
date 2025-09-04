let socket = io();
let peers = {}; // peers por room
let roomName = null;
let logEl = null;
let dc = null;  // data channel común si hay 1-1 (demo simple)

function log(msg) {
  if (!logEl) logEl = document.getElementById('log');
  logEl.innerHTML += msg + "<br/>";
  logEl.scrollTop = logEl.scrollHeight;
}

function join() {
  roomName = document.getElementById('room').value || 'default';
  socket.emit('join', { room: roomName });
  log("Conectado a sala: " + roomName);

  // Creamos peer como iniciador
  createPeer(true);
}

function leave() {
  if (roomName) {
    socket.emit('leave', { room: roomName });
    roomName = null;
  }
  for (const id in peers) {
    peers[id].destroy();
  }
  peers = {};
  log("Saliste de la sala");
}

function createPeer(initiator=false) {
  const peer = new SimplePeer({
    initiator,
    trickle: true
  });

  peer.on('signal', data => {
    // enviamos señal por socket
    socket.emit('signal', { room: roomName, data });
  });

  peer.on('connect', () => {
    log("Conexión P2P establecida ✅");
    dc = peer; // data channel
  });

  peer.on('data', buffer => {
    // Mensajes o archivo (chunked)
    try {
      const msg = new TextDecoder().decode(buffer);
      if (msg.startsWith("FILEMETA::")) {
        const meta = JSON.parse(msg.replace("FILEMETA::", ""));
        peers._fileMeta = meta;
        peers._fileChunks = [];
        log(`Recibiendo archivo: ${meta.name} (${meta.size} bytes)`);
      } else if (msg === "FILEEND") {
        const blob = new Blob(peers._fileChunks);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = peers._fileMeta.name;
        a.click();
        URL.revokeObjectURL(url);
        log("Archivo recibido y descargado ✅");
        peers._fileChunks = [];
        peers._fileMeta = null;
      } else {
        // chunk binario o texto normal
        if (peers._fileMeta) {
          // asumimos que no es UTF-8 si llega aquí
          peers._fileChunks.push(buffer);
        } else {
          log("Peer: " + msg);
        }
      }
    } catch (e) {
      // binario puro (archivo)
      if (peers._fileMeta) peers._fileChunks.push(buffer);
    }
  });

  peers.main = peer;
}

socket.on('signal', payload => {
  if (!peers.main) {
    createPeer(false);
  }
  peers.main.signal(payload.data);
});

socket.on('system', data => {
  log("[sistema] " + data.msg);
});

function sendMsg() {
  const m = document.getElementById('msg').value;
  if (dc && dc.connected) {
    dc.send(m);
    log("Tú: " + m);
    document.getElementById('msg').value = '';
  } else {
    log("Aún no hay conexión P2P");
  }
}

function sendFile() {
  const file = document.getElementById('fileInput').files[0];
  if (!file) return;
  if (!(dc && dc.connected)) {
    return log("Aún no hay conexión P2P");
  }
  // metadata
  const meta = { name: file.name, size: file.size, type: file.type };
  dc.send("FILEMETA::" + JSON.stringify(meta));

  const chunkSize = 16 * 1024; // 16 KB
  const reader = file.stream().getReader();
  function pump() {
    reader.read().then(({done, value}) => {
      if (done) {
        dc.send("FILEEND");
        log("Archivo enviado ✅");
        return;
      }
      dc.send(value);
      pump();
    });
  }
  pump();
}
