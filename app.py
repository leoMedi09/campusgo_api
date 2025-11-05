from flask import Flask, jsonify
# Use package-relative imports so the app can be loaded by gunicorn
from routes.usuario import ws_usuario
from routes.vehiculo import ws_vehiculo
from routes.reserva import ws_reserva
import urllib.request
import socket
import os
from .conexionBD import Conexion
import uuid
import datetime
from .config import Config

app = Flask(__name__)
app.register_blueprint(ws_usuario)
app.register_blueprint(ws_vehiculo)
app.register_blueprint(ws_reserva)




def home():
    # Return a short message including DEPLOY_VERSION when available so we can
    # detect which commit is live on Render.
    try:
        base = os.path.dirname(__file__)
        path = os.path.join(base, '..', 'DEPLOY_VERSION')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                v = f.read().strip()
            return f'CampusGO - Running API Restful (version: {v})'
    except Exception:
        pass
    return 'CampusGO - Running API Restful'
def whoami():
    """Dev-only endpoint that returns the public IP address of this container.
    Useful to discover the outbound IP for whitelisting.
    """
    try:
        with urllib.request.urlopen('https://ifconfig.me/ip', timeout=5) as r:
            ip = r.read().decode().strip()
    except Exception as e:
        # fallback: try to get local socket name (not the public IP but useful)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            ip = f'error: {str(e)}'

    return jsonify({'ip': ip})


if Config.EXPOSE_DEBUG_ROUTES:
    @app.route('/whoami', methods=['GET'])
    def whoami():
        """Dev-only endpoint that returns the public IP address of this container.
        Only enabled when EXPOSE_DEBUG_ROUTES=True.
        """
        try:
            with urllib.request.urlopen('https://ifconfig.me/ip', timeout=5) as r:
                ip = r.read().decode().strip()
        except Exception as e:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
                s.close()
            except Exception:
                ip = f'error: {str(e)}'

        return jsonify({'ip': ip})


@app.route('/health-db', methods=['GET'])
def health_db():
    """Simple health check that tries to open a DB connection and run SELECT 1."""
    try:
        db = Conexion()
        cur = db.open.cursor()
        cur.execute('SELECT 1 as ok')
        row = cur.fetchone()
        return jsonify({'ok': True, 'result': row}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


if Config.EXPOSE_DEBUG_ROUTES:
    @app.route('/__db_conn_trace__', methods=['GET'])
    def db_conn_trace():
        """Dev-only endpoint: intenta conectarse a la base de datos y devuelve
        el traceback completo en caso de error. Solo activa cuando
        EXPOSE_DEBUG_ROUTES=True.
        """
        import traceback
        try:
            db = Conexion()
            cur = db.open.cursor()
            cur.execute('SELECT 1 as ok')
            row = cur.fetchone()
            return jsonify({'ok': True, 'result': row}), 200
        except Exception as e:
            tb = traceback.format_exc()
            return jsonify({'ok': False, 'error': str(e), 'traceback': tb}), 500


if Config.EXPOSE_DEBUG_ROUTES:
    @app.route('/__debug__routes_env', methods=['GET'])
    def debug_routes_env():
        """Temporary debug endpoint that is only enabled when
        EXPOSE_DEBUG_ROUTES=True. Returns registered routes and a masked
        summary of DB_* env vars. This helps avoid accidental exposure in
        production environments.
        """
        def mask(v: str) -> str:
            if v is None:
                return None
            if len(v) <= 6:
                return '***'
            return v[:3] + '...' + v[-3:]

        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({'rule': str(rule), 'methods': sorted(list(rule.methods))})

        db_env = {}
        for k, v in os.environ.items():
            if k.startswith('DB_'):
                db_env[k] = {'present': True, 'masked': mask(v), 'length': len(v)}

        for name in ('DB_USE_SSL', 'DB_SSL_CA_B64', 'DB_SSL_CA_PATH', 'DB_HOST', 'DB_USER', 'DB_NAME'):
            if name not in db_env:
                db_env[name] = {'present': False}

        return jsonify({'routes': routes, 'db_env': db_env}), 200


def version():
    """Return the contents of DEPLOY_VERSION if present (helpful to know which commit is live)."""
    try:
        base = os.path.dirname(__file__)
        path = os.path.join(base, '..', 'DEPLOY_VERSION')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                v = f.read().strip()
            return jsonify({'version': v}), 200
    except Exception:
        pass
    return jsonify({'version': 'unknown'}), 200
def i_am_live():
    """Return the live token printed at startup (non-secret, for debugging only)."""
    try:
        base = os.path.dirname(__file__)
        path = os.path.join(base, '..', 'DEPLOY_VERSION')
        dv = None
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                dv = f.read().strip()
    except Exception:
        dv = None

    token = f"{dv or 'noversion'}-unknown"
    # Try to read LIVE_TOKEN printed at import-time if present in module globals
    try:
        token = globals().get('LIVE_TOKEN', token)
    except Exception:
        pass

    return jsonify({'live_token': token}), 200
    
    @app.route('/__version__', methods=['GET'])
    def version():
        """Return the contents of DEPLOY_VERSION if present (helpful to know which commit is live)."""
        try:
            base = os.path.dirname(__file__)
            path = os.path.join(base, '..', 'DEPLOY_VERSION')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    v = f.read().strip()
                return jsonify({'version': v}), 200
        except Exception:
            pass
        return jsonify({'version': 'unknown'}), 200


    @app.route('/__i_am_live__', methods=['GET'])
    def i_am_live():
        """Return the live token printed at startup (for debugging only)."""
        try:
            base = os.path.dirname(__file__)
            path = os.path.join(base, '..', 'DEPLOY_VERSION')
            dv = None
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    dv = f.read().strip()
        except Exception:
            dv = None

        token = f"{dv or 'noversion'}-unknown"
        try:
            token = globals().get('LIVE_TOKEN', token)
        except Exception:
            pass

        return jsonify({'live_token': token}), 200


#Iniciar el servicio web con Flask (solo para desarrollo local)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3006))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('1', 'true')
    app.run(port=port, debug=debug, host='0.0.0.0')


# Log registered routes and DB_* env presence at startup so they appear in Render logs.
try:
    # Limited startup logs to avoid accidental leak of secrets. We still
    # print the registered routes (useful) and a non-sensitive deploy token.
    routes_list = [str(r) for r in app.url_map.iter_rules()]
    print('STARTUP: Registered routes:', routes_list)
    deploy_ver = None
    try:
        base = os.path.dirname(__file__)
        path = os.path.join(base, '..', 'DEPLOY_VERSION')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                deploy_ver = f.read().strip()
    except Exception:
        deploy_ver = None

    LIVE_TOKEN = f"{deploy_ver or 'noversion'}-{uuid.uuid4().hex[:8]}-{datetime.datetime.utcnow().strftime('%y%m%d%H%M%S')}"
    print('STARTUP: LIVE_TOKEN=', LIVE_TOKEN)
except Exception as _e:
    print('STARTUP: route logging failed', str(_e))