# Import the create_app function from the app package
from app import create_app
from config import DevelopmentConfig

# Create the Flask app and the SocketIO instance using the app factory
app, socketio = create_app(config_class=DevelopmentConfig)

# This block ensures that the server is started only when the script is executed directly
if __name__ == '__main__':
    # Run the app with SocketIO support
    # The app will be accessible from any IP address on the network on port 5000
    socketio.run(app, host='0.0.0.0', port=5000)

