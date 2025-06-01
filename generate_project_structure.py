import os
import sys


def generate_structure(startpath, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Estructura del proyecto: {os.path.basename(os.path.abspath(startpath))}\n")
        f.write("=" * 50 + "\n\n")

        exclude_dirs = ['__pycache__', '.git', '.idea', 'venv', '.venv', 'env', 'node_modules']
        exclude_files = ['.pyc', '.pyo', '.pyd', '.git', '.DS_Store']

        for root, dirs, files in os.walk(startpath):
            # Excluir directorios no deseados
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            # Calcular nivel para indentación
            level = root.replace(startpath, '').count(os.sep)
            indent = '│   ' * level
            f.write(f"{indent}├── {os.path.basename(root)}/\n")

            # Mostrar archivos
            subindent = '│   ' * (level + 1)
            for file in sorted(files):
                # Excluir archivos no deseados
                if not any(file.endswith(ext) for ext in exclude_files):
                    f.write(f"{subindent}├── {file}\n")


if __name__ == "__main__":
    output_file = "estructura_proyecto.txt"
    generate_structure(".", output_file)
    print(f"Estructura generada en {output_file}")
