from flask import Flask
from routes.usuario import ws_usuario
from routes.vehiculo import ws_vehiculo
from routes.reserva import ws_reserva

app = Flask(__name__)
app.register_blueprint(ws_usuario)
app.register_blueprint(ws_vehiculo)
app.register_blueprint(ws_reserva)


@app.route('/')
def home():
    return 'CampusGO - Running API Restful'

#Iniciar el servicio web con Flask
if __name__ == '__main__':
    app.run(port=3007, debug=True, host='0.0.0.0')