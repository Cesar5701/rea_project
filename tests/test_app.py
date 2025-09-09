import numpy as np
from io import BytesIO

# --- Public Page Access Tests ---

def test_index_page_loads(client):
    """Tests that the home page loads correctly for any visitor."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Bienvenido a la Plataforma de Recursos Educativos Abiertos" in response.data
    assert b"Iniciar Sesión" in response.data  # "Iniciar Sesión"

def test_login_page_loads(client):
    """Tests that the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Iniciar Sesión" in response.data

def test_register_page_loads(client):
    """Tests that the registration page loads correctly."""
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Crear una Cuenta" in response.data

# --- Protected Routes Tests ---

def test_protected_routes_redirect_anonymous_user(client):
    """
    Tests that protected routes redirect an anonymous user
    to the login page.
    """
    protected_routes = ['/nuevo', '/recursos', '/buscar_semantico', '/webrtc']
    for route in protected_routes:
        response = client.get(route, follow_redirects=True)
        assert response.status_code == 200
        assert b"Iniciar Sesión" in response.data, f"La ruta {route} no redirigio al login."

# --- Authentication Flow Tests ---

def test_full_auth_flow(client):
    """
    Tests the complete user flow: registration, logout, login,
    and access to a protected route.
    """
    # 1. Register a new user
    response_register = client.post('/register', data={
        'email': 'testuser@alumno.buap.mx',
        'password': 'PasswordFuerte123!'
    }, follow_redirects=True)
    
    assert response_register.status_code == 200
    assert b"Registro exitoso!" in response_register.data
    assert b"inicia sesión" in response_register.data # "inicia sesión"

    # 2. Trying to register the same user again should fail
    response_register_fail = client.post('/register', data={
        'email': 'testuser@alumno.buap.mx',
        'password': 'PasswordFuerte123!'
    }, follow_redirects=True)
    assert response_register_fail.status_code == 200
    assert b"Ese correo electrónico ya está registrado." in response_register_fail.data

    # 3. Log out (ensures the session is cleared if it exists)
    response_logout = client.get('/logout', follow_redirects=True)
    assert response_logout.status_code == 200
    assert b"Iniciar Sesión" in response_logout.data

    # 4. Logging in with incorrect credentials should fail
    response_login_fail = client.post('/login', data={
        'email': 'testuser@alumno.buap.mx',
        'password': 'passwordincorrecto'
    }, follow_redirects=True)
    assert response_login_fail.status_code == 200
    assert b"Correo o contraseña incorrectos." in response_login_fail.data

    # 5. Log in with the correct credentials
    response_login = client.post('/login', data={
        'email': 'testuser@alumno.buap.mx',
        'password': 'PasswordFuerte123!'
    }, follow_redirects=True)
    assert response_login.status_code == 200
    assert b"Bienvenido, <strong>testuser</strong>" in response_login.data
    assert b"Cerrar Sesión" in response_login.data # "Cerrar Sesión"

    # 6. Accessing a protected route should now work
    response_nuevo = client.get('/nuevo')
    assert response_nuevo.status_code == 200
    assert b"Añadir Nuevo Recurso" in response_nuevo.data # "Añadir Nuevo Recurso"

# --- Core Functionality Tests (with Mocking) ---

def test_create_new_resource_with_mocking(client, mocker):
    """
    Tests the creation of a new resource, mocking calls
    to external services like IPFS and NLP models so that the tests
    are fast and do not depend on external services.
    """
    # 1. Mock the external functions that are called from the /nuevo route
    mocker.patch('app.upload_to_ipfs', return_value=('fake_cid_123', 'https://fake_cid_123.ipfs.w3s.link/test.txt'))
    mocker.patch('app.clasificar_texto', return_value='matemáticas')
    # Make generar_embedding return a real numpy array
    fake_embedding = np.random.rand(768).astype(np.float32)
    mocker.patch('app.generar_embedding', return_value=fake_embedding)
    # Mock the add to the vector DB, since we don't need to test ChromaDB here
    mocker.patch('app.add_embedding_to_chroma', return_value=None)
    
    # 2. We need to be logged in to create a resource
    client.post('/register', data={'email': 'creator@alumno.buap.mx', 'password': 'PasswordCreator123!'})
    client.post('/login', data={'email': 'creator@alumno.buap.mx', 'password': 'PasswordCreator123!'})
    
    # 3. Prepare the form data, including a simulated file
    form_data = {
        'titulo': 'Introducción al Cálculo',
        'descripcion': 'Un recurso sobre derivadas e integrales.',
        'archivo': (BytesIO(b"Este es el contenido del archivo de prueba."), 'calculo_intro.txt')
    }

    # 4. Send the POST request to create the resource
    response = client.post(
        '/nuevo', 
        data=form_data, 
        content_type='multipart/form-data',
        follow_redirects=True
    )

    # 5. Verify that everything worked as expected
    assert response.status_code == 200
    # Success message
    assert b"Recurso guardado y clasificado: matemáticas" in response.data
    # The new resource should appear on the resources page
    assert b"Introducción al Cálculo" in response.data # "Introducción al Cálculo"
    assert b"Un recurso sobre derivadas e integrales." in response.data
