import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import sys
import subprocess

def get_encryption_key():
    """Obtiene y deriva la clave desde la variable de entorno KEY_CODE"""
    try:
        key_code = os.environ.get('KEY_CODE')
        if not key_code:
            raise ValueError("KEY_CODE no está definida en las variables de entorno")
        
        
        # Decodifica la clave base64
        key = base64.urlsafe_b64decode(key_code)
        
        # Aseguramos que tenga exactamente 32 bytes
        if len(key) != 32:
            # Si no es exactamente 32 bytes, derivamos una clave usando PBKDF2
            salt = b'fixed_salt_for_github'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(key_code.encode())
        else:
        
        return key
    except Exception as e:
        print(f"✗ Error al procesar la clave: {e}")
        sys.exit(1)

def is_encrypted_file(file_path):
    """Verifica si un archivo está encriptado intentando decodificarlo como base64"""
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
        
        # Intenta decodificar el contenido como base64
        decoded = base64.b64decode(content)
        # Verifica que el contenido decodificado tenga al menos 16 bytes (IV)
        return len(decoded) >= 16
    except:
        return False

def decrypt_file_in_place(file_path, key):
    """Descifra un archivo encriptado y lo sobrescribe con el contenido desencriptado"""
    try:
        
        # Verifica si el archivo de entrada existe y no está vacío
        if not os.path.exists(file_path):
            return True
            
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return True
            
        
        # Lee el archivo cifrado (que está en Base64)
        with open(file_path, 'r') as file:
            encrypted_data_b64 = file.read()
        
        # Decodifica de Base64 a bytes
        try:
            encrypted_data = base64.b64decode(encrypted_data_b64)
        except Exception as e:
            return False
            
        # Verifica que tenga al menos 16 bytes (tamaño del IV)
        if len(encrypted_data) < 16:
            return True
            
        # Separa el IV y el ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Configura el descifrador
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Descifra el contenido
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Elimina el padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        # Guarda el archivo descifrado (sobrescribiendo el original)
        with open(file_path, 'wb') as file:
            file.write(plaintext)
        
        output_size = os.path.getsize(file_path)
        
        return True
    except Exception as e:
        print(f"✗ Error al descifrar: {e}")
        return False

def main():
    # Obtener la clave
    key = get_encryption_key()
    
    # Lista de archivos y directorios a excluir
    exclude_files = ['main.py', 'requirements.txt']
    exclude_dirs = ['.git', '__pycache__', 'venv', 'env']
    
    print("Buscando archivos encriptados en el repositorio...")
    
    # Recorrer todos los archivos en el directorio actual y subdirectorios
    for root, dirs, files in os.walk('.'):
        # Excluir directorios no deseados
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file in exclude_files:
                continue
                
            file_path = os.path.join(root, file)
            
            # Verificar si el archivo está encriptado
            if is_encrypted_file(file_path):
                print(f"Archivo encriptado encontrado: {file_path}")
                # Desencriptar el archivo
                decrypt_file_in_place(file_path, key)
    
    # Ejecutar activebot.py después de desencriptar
    print("Ejecutando activebot.py...")
    try:
        result = subprocess.run([sys.executable, 'activebot.py'], check=True)
    except FileNotFoundError:
        print("✗ activebot.py no encontrado")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error al ejecutar activebot.py: {e}")
    except Exception as e:
        print(f"✗ Error inesperado: {e}")

if __name__ == "__main__":
    main()
