import os
import sys
import importlib.util
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Cargar variables de entorno
load_dotenv()

# Configuración
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
ENCRYPTED_EXTENSION = '.encrypted'
MAIN_SCRIPT = 'bot_main'  # Nombre del módulo principal (sin extensión)

def decrypt_file(encrypted_path, output_path):
    """Desencripta un archivo y lo guarda en la ruta especificada"""
    try:
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        cipher = Fernet(ENCRYPTION_KEY)
        decrypted_data = cipher.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        return True
    except Exception as e:
        print(f"Error desencriptando {encrypted_path}: {e}")
        return False

def load_module(module_name, file_path):
    """Carga un módulo desde una ruta específica"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error cargando módulo {module_name}: {e}")
        return None

def main():
    # Verificar si la clave de encriptación está configurada
    if not ENCRYPTION_KEY:
        print("ERROR: No se encontró ENCRYPTION_KEY en las variables de entorno")
        sys.exit(1)
    
    # Ruta del script principal encriptado y no encriptado
    encrypted_main = f"{MAIN_SCRIPT}{ENCRYPTED_EXTENSION}"
    plain_main = f"{MAIN_SCRIPT}.py"
    
    # Determinar qué versión del script principal usar
    main_script_path = None
    
    if os.path.exists(encrypted_main):
        # Desencriptar y cargar la versión encriptada
        temp_decrypted = "temp_decrypted.py"
        if decrypt_file(encrypted_main, temp_decrypted):
            main_script_path = temp_decrypted
            print("✓ Script principal desencriptado correctamente")
        else:
            print("✗ Error desencriptando el script principal")
    elif os.path.exists(plain_main):
        # Usar la versión no encriptada
        main_script_path = plain_main
        print("✓ Usando script principal no encriptado")
    else:
        print("✗ No se encontró ningún script principal")
        sys.exit(1)
    
    # Cargar y ejecutar el módulo principal
    if main_script_path:
        main_module = load_module(MAIN_SCRIPT, main_script_path)
        
        if main_module and hasattr(main_module, 'main'):
            # Ejecutar la función main del módulo
            main_module.main()
        else:
            print("✗ El script principal no tiene una función 'main'")
    
    # Limpiar archivo temporal si existe
    if 'temp_decrypted' in locals() and os.path.exists('temp_decrypted.py'):
        os.remove('temp_decrypted.py')

if __name__ == "__main__":
    main()
