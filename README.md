# Gestion d'inventaire avec Flask

## Instructions

1. Cloner le dépôt Git :
   ```bash
   git clone https://github.com/badr2e/M1_GestionInventaire.git
   ```

2. Aller dans le dossier cloné et installer les dépendances :
   ```bash
   cd M1_GestionInventaire
   pip install -r requirements.txt
   ```

3. Créer et configurer le fichier .env avec les informations suivantes de votre serveur MySQL
    ```plaintext
    MYSQL_HOST=
    MYSQL_USER=
    MYSQL_PASSWORD=
    MYSQL_DB=
    SECRET_KEY=
    ```

4. Lancer le fichier
    ```bash
    python init_db.py
    python app.py
    ```