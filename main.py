import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import sys

def get_encryption_key():
    """Obtiene y deriva la clave desde la variable de entorno KEY_CODE"""
    try:
        key_code = os.environ.get('KEY_CODE')
        if not key_code:
            raise ValueError("KEY_CODE no está definida en las variables de entorno")
        
        print("✓ KEY_CODE encontrada en variables de entorno")
        
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
            print("✓ Clave derivada usando PBKDF2")
        else:
            print("✓ Clave tiene el tamaño correcto (32 bytes)")
        
        return key
    except Exception as e:
        print(f"✗ Error al procesar la clave: {e}")
        sys.exit(1)

def is_encrypted_file(content):
    """Intenta determinar si el contenido está encriptado verificando si es base64 válido"""
    try:
        # Intenta decodificar el contenido como base64
        decoded = base64.b64decode(content)
        # Verifica que el contenido decodificado tenga al menos 16 bytes (IV)
        return len(decoded) >= 16
    except:
        return False

def decrypt_file_content(encrypted_content, key):
    """Descifra contenido en memoria usando AES-256 en modo CBC"""
    try:
        # Decodifica de Base64 a bytes
        encrypted_data = base64.b64decode(encrypted_content)
        
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
        
        return plaintext.decode('utf-8')
    except Exception as e:
        print(f"✗ Error al descifrar contenido: {e}")
        return None

def main():
    # Obtener la clave de encriptación
    key = get_encryption_key()
    
    # Recorrer todos los archivos del directorio actual y subdirectorios
    for root, dirs, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Saltar archivos específicos
            if file in ['main.py', 'activebot.py']:
                continue
                
            try:
                # Leer el contenido del archivo
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verificar si el archivo parece estar encriptado
                if is_encrypted_file(content):
                    print(f"Procesando archivo encriptado: {file_path}")
                    
                    # Desencriptar el contenido
                    decrypted_content = decrypt_file_content(content, key)
                    
                    if decrypted_content is not None:
                        # Sobrescribir el archivo con el contenido desencriptado
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(decrypted_content)
                        print(f"✓ Archivo desencriptado: {file_path}")
                    else:
                        print(f"✗ Error al desencriptar: {file_path}")
            except Exception as e:
                print(f"✗ Error procesando archivo {file_path}: {e}")
                continue
    
    # Ejecutar activebot.py después de desencriptar
    print("Ejecutando activebot.py...")
    try:
        os.system('python activebot.py')
    except Exception as e:
        print(f"Error ejecutando activebot.py: {e}")

if __name__ == "__main__":
    main()
