import os
import json

PATCHES_DIR = "public/data/patches"
INDEX_FILE = "public/data/index.json"

def main():
    # 1. Charger le fichier index.json qui contient les bonnes relations titre/date/fichier
    if not os.path.exists(INDEX_FILE):
        print(f"Erreur : Le fichier {INDEX_FILE} est introuvable.")
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index_data = json.load(f)

    print(f"Chargement de l'index réussi : {len(index_data)} patchs trouvés.")
    updated_count = 0

    # 2. Parcourir chaque élément de l'index
    for item in index_data:
        file_name = item.get("file")
        correct_date = item.get("date")

        if not file_name or not correct_date:
            continue

        # Construire le chemin vers le fichier du patch
        patch_file_path = os.path.join(PATCHES_DIR, file_name)

        # Vérifier si le fichier du patch existe bien dans le dossier public/data/patches
        if os.path.exists(patch_file_path):
            with open(patch_file_path, "r", encoding="utf-8") as f:
                try:
                    patch_data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Erreur de lecture JSON sur le fichier : {file_name}")
                    continue

            old_date = patch_data.get("patch_date")

            # Si la date dans le fichier du patch est différente de celle de l'index, on met à jour
            if old_date != correct_date:
                patch_data["patch_date"] = correct_date

                # Sauvegarder les modifications dans le fichier du patch
                with open(patch_file_path, "w", encoding="utf-8") as f:
                    json.dump(patch_data, f, ensure_ascii=False, indent=2)
                
                print(f"Mis à jour {file_name} : {old_date} -> {correct_date}")
                updated_count += 1
        else:
            print(f"Fichier manquant dans le dossier : {file_name}")

    print(f"\nTerminé ! {updated_count} fichiers de patchs ont été mis à jour avec succès.")

if __name__ == "__main__":
    main()