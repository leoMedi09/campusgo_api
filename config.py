import os


class Config:
    DB_HOST = os.environ.get('DB_HOST', 'gateway01.us-east-1.prod.aws.tidbcloud.com')
    DB_USER = os.environ.get('DB_USER', '2FaYsF4hcm2iFVK.root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'KAWIpAJ29lNiPfk7')
    DB_NAME = os.environ.get('DB_NAME', 'campusgo')
    DB_PORT = int(os.environ.get('DB_PORT', 4000))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave_secreta_para_jwt')

    # SSL/TLS for databases like TiDB Cloud
    # Set DB_USE_SSL to 'true' (case-insensitive) to enable SSL verification.
    DB_USE_SSL = str(os.environ.get('DB_USE_SSL', 'true')).lower() in ('1', 'true', 'yes')
    # You can provide the CA certificate either as a file path in DB_SSL_CA_PATH
    # or as a base64-encoded PEM string in DB_SSL_CA_B64.
    DB_SSL_CA_PATH = os.environ.get('DB_SSL_CA_PATH', '')
    
    # Default: read CA from db_ssl_ca_b64.txt if present and env var not set
    _default_ca_b64 = ''
    if not os.environ.get('DB_SSL_CA_B64'):
        ca_file_path = os.path.join(os.path.dirname(os.path.dirname(file_)), 'db_ssl_ca_b64.txt')
        if os.path.exists(_ca_file_path):
            try:
                with open(_ca_file_path, 'r') as f:
                    _default_ca_b64 = f.read().strip()
            except Exception:
                pass
    DB_SSL_CA_B64 = os.environ.get('DB_SSL_CA_B64', _default_ca_b64)

    # Controls whether temporary debug endpoints are exposed (default: False)
    EXPOSE_DEBUG_ROUTES = str(os.environ.get('EXPOSE_DEBUG_ROUTES', 'false')).lower() in ('1', 'true', 'yes')