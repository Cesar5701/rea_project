import numpy as np
from io import BytesIO

# --- Pruebas de Acceso a Páginas Públicas ---

def test_index_page_loads(client):
    """Prueba que la página de inicio se carga correctamente para cualquier visitante."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Bienvenido a la Plataforma de Recursos Educativos Abiertos" in response.data
    assert b"Iniciar Sesi\xc3\xb3n" in response.data  # "Iniciar Sesión"

def test_login_page_loads(client):
    """Prueba que la página de login se carga correctamente."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Iniciar Sesi\xc3\xb3n" in response.data

def test_register_page_loads(client):
    """Prueba que la página de registro se carga correctamente."""
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Crear una Cuenta" in response.data

# --- Pruebas de Rutas Protegidas ---

def test_protected_routes_redirect_anonymous_user(client):
    """
    Prueba que las rutas protegidas redirigen a un usuario anónimo
    a la página de inicio de sesión.
    """
    protected_routes = ['/nuevo', '/recursos', '/buscar_semantico', '/webrtc']
    for route in protected_routes:
        response = client.get(route, follow_redirects=True)
        assert response.status_code == 200
        assert b"Iniciar Sesi\xc3\xb3n" in response.data, f"La ruta {route} no redirigio al login."

# --- Pruebas del Flujo de Autenticación ---

def test_full_auth_flow(client):
    """
    Prueba el flujo completo de un usuario: registro, logout, login,
    y acceso a una ruta protegida.
    """
    # 1. Registrar un nuevo usuario
    response_register = client.post('/register', data={
        'email': 'testuser@alumno.buap.mx',
        'password': 'PasswordFuerte123!'
    }, follow_redirects=True)
    
    assert response_register.status_code == 200
    assert b"Registro exitoso!" in response_register.data
    assert b"inicia sesi\xc3\xb3n" in response_register.data # "inicia sesión"

    # 2. Intentar registrar al mismo usuario de nuevo debe fallar
    response_register_fail = client.post('/register', data={
        'email': 'testuser@alumno.buap.mx',
        'password': 'PasswordFuerte123!'
    }, follow_redirects=True)
    assert response_register_fail.status_code == 200
    assert b"Ese correo electr\xc3\xb3nico ya est\xc3\xa1 registrado." in response_register_fail.data

    # 3. Hacer logout (asegura que la sesión se limpia si existiera)
    response_logout = client.get('/logout', follow_redirects=True)
    assert response_logout.status_code == 200
    assert b"Iniciar Sesi\xc3\xb3n" in response_logout.data

    # 4. Iniciar sesión con credenciales incorrectas debe fallar
    response_login_fail = client.post('/login', data={
        'email': 'testuser@alumno.buap.mx',
        'password': 'passwordincorrecto'
    }, follow_redirects=True)
    assert response_login_fail.status_code == 200
    assert b"Correo o contrase\xc3\xb1a incorrectos." in response_login_fail.data

    # 5. Iniciar sesión con las credenciales correctas
    response_login = client.post('/login', data={
        'email': 'testuser@alumno.buap.mx',
        'password': 'PasswordFuerte123!'
    }, follow_redirects=True)
    assert response_login.status_code == 200
    assert b"Bienvenido, <strong>testuser</strong>" in response_login.data
    assert b"Cerrar Sesi\xc3\xb3n" in response_login.data # "Cerrar Sesión"

    # 6. Acceder a una ruta protegida ahora debe funcionar
    response_nuevo = client.get('/nuevo')
    assert response_nuevo.status_code == 200
    assert b"A\xc3\xb1adir Nuevo Recurso" in response_nuevo.data # "Añadir Nuevo Recurso"

# --- Pruebas de Funcionalidad Principal (con Mocking) ---

def test_create_new_resource_with_mocking(client, mocker):
    """
    Prueba la creación de un nuevo recurso, simulando (mocking) las llamadas
    a servicios externos como IPFS y los modelos de NLP para que las pruebas
    sean rápidas y no dependan de servicios externos.
    """
    # 1. Mockear las funciones externas que se llaman desde la ruta /nuevo
    mocker.patch('app.upload_to_ipfs', return_value=('fake_cid_123', 'https://fake_cid_123.ipfs.w3s.link/test.txt'))
    mocker.patch('app.clasificar_texto', return_value='matemáticas')
    # Hacemos que generar_embedding devuelva un array de numpy real
    fake_embedding = np.random.rand(768).astype(np.float32)
    mocker.patch('app.generar_embedding', return_value=fake_embedding)
    # Mockeamos el add a la BD vectorial, ya que no necesitamos probar ChromaDB aquí
    mocker.patch('app.add_embedding_to_chroma', return_value=None)
    
    # 2. Necesitamos estar logueados para crear un recurso
    client.post('/register', data={'email': 'creator@alumno.buap.mx', 'password': 'PasswordCreator123!'})
    client.post('/login', data={'email': 'creator@alumno.buap.mx', 'password': 'PasswordCreator123!'})
    
    # 3. Preparar los datos del formulario, incluyendo un archivo simulado
    form_data = {
        'titulo': 'Introducción al Cálculo',
        'descripcion': 'Un recurso sobre derivadas e integrales.',
        'archivo': (BytesIO(b"Este es el contenido del archivo de prueba."), 'calculo_intro.txt')
    }

    # 4. Enviar la petición POST para crear el recurso
    response = client.post(
        '/nuevo', 
        data=form_data, 
        content_type='multipart/form-data',
        follow_redirects=True
    )

    # 5. Verificar que todo funcionó como se esperaba
    assert response.status_code == 200
    # Mensaje de éxito
    assert b"Recurso guardado y clasificado: matem\xc3\xa1ticas" in response.data
    # El nuevo recurso debe aparecer en la página de recursos
    assert b"Introducci\xc3\xb3n al C\xc3\xa1lculo" in response.data # "Introducción al Cálculo"
    assert b"Un recurso sobre derivadas e integrales." in response.data
