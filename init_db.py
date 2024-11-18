import sqlite3
import os

# Chemin vers la base de données SQLite
DATABASE_PATH = os.getenv('DATABASE_PATH', 'gestion_inventaire.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Créer la table `user`
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_login TEXT NOT NULL,
        user_password TEXT NOT NULL,
        user_mail TEXT UNIQUE NOT NULL,
        user_date_new DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_date_login DATETIME,
        user_compte_id INTEGER DEFAULT 0
    )
    ''')

    # Créer la table `item_types`
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS item_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT NOT NULL
    )
    ''')


    # Ajouter des types d'objets par défaut
    cursor.execute('''insert into item_types (type_name) values ('potion')''')
    cursor.execute('''insert into item_types (type_name) values ('plante')''')
    cursor.execute('''insert into item_types (type_name) values ('arme')''')
    cursor.execute('''insert into item_types (type_name) values ('clé')''')
    cursor.execute('''insert into item_types (type_name) values ('armure')''')


    # Créer la table `inventory` associée à chaque utilisateur
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        type_id INTEGER,
        quantity INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES user(user_id),
        FOREIGN KEY (type_id) REFERENCES item_types(id)
    )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("Base de données initialisée avec succès.")

if __name__ == '__main__':
    init_db()
