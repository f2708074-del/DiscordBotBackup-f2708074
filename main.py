import os
import sys
import importlib.util
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
ENCRYPTED_EXTENSION = '.encrypted'

def decrypt_file(encrypted_path, output_path):
    """Desencripta un archivo y lo guarda en la ruta especificada"""
    try:
        cipher = Fernet(ENCRYPTION_KEY)
        
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = cipher.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        print(f"✓ {encrypted_path} desencriptado correctamente")
        return True
    except Exception as e:
        print(f"✗ Error desencriptando {encrypted_path}: {e}")
        return False

def decrypt_all_files():
    """Desencripta todos los archivos con extensión .encrypted en el directorio"""
    if not ENCRYPTION_KEY:
        print("ERROR: No se encontró ENCRYPTION_KEY en las variables de entorno")
        return False
    
    decrypted_count = 0
    error_count = 0
    
    # Recorrer todos los archivos en el directorio actual
    for filename in os.listdir('.'):
        if filename.endswith(ENCRYPTED_EXTENSION):
            # Generar el nombre del archivo desencriptado
            output_filename = filename[:-len(ENCRYPTED_EXTENSION)]
            
            # Desencriptar el archivo
            if decrypt_file(filename, output_filename):
                decrypted_count += 1
            else:
                error_count += 1
    
    print(f"\nDesencriptación completada: {decrypted_count} archivos desencriptados, {error_count} errores")
    return error_count == 0

def run_active_bot():
    """Ejecuta el ActiveBot.py"""
    if not os.path.exists('ActiveBot.py'):
        print("ERROR: No se encontró ActiveBot.py")
        return False
    
    try:
        # Importar y ejecutar ActiveBot
        spec = importlib.util.spec_from_file_location("ActiveBot", "ActiveBot.py")
        active_bot = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(active_bot)
        
        # Verificar si tiene una función main
        if hasattr(active_bot, 'main'):
            active_bot.main()
            return True
        else:
            print("ERROR: ActiveBot.py no tiene una función 'main'")
            return False
    except Exception as e:
        print(f"ERROR ejecutando ActiveBot.py: {e}")
        return False

def main():
    """Función principal"""
    print("Iniciando proceso de desencriptación...")
    
    # Desencriptar todos los archivos
    success = decrypt_all_files()
    
    if success:
        print("\nEjecutando ActiveBot...")
        run_active_bot()
    else:
        print("No se pudo completar la desencriptación, abortando...")
        sys.exit(1)

if __name__ == "__main__":
    main()
