import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import click

# Charger les variables d'environnement
load_dotenv()

# Créer une instance de l'application Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Chemin vers la base de données SQLite
DATABASE_PATH = os.getenv('DATABASE_PATH', 'gestion_inventaire.db')


# Fonction pour obtenir une connexion SQLite
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Pour obtenir des résultats sous forme de dictionnaire
    return conn


# Fonction pour initialiser la base de données SQLite
def init_db():
    print("Initialisation de la base de données...")
    conn = get_db_connection()
    cursor = conn.cursor()

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

    # Créer la table `inventory`
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type_id INTEGER,
        quantity INTEGER DEFAULT 0,
        FOREIGN KEY (type_id) REFERENCES item_types(id)
    )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("Tables créées avec succès.")


# Route principale : affichage de l'inventaire
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT inventory.id AS item_id, 
               inventory.name AS item_name, 
               item_types.type_name AS item_type, 
               inventory.quantity AS item_quantity 
        FROM inventory 
        LEFT JOIN item_types ON inventory.type_id = item_types.id
    ''')
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('inventory.html', items=items)


# Route pour ajouter un nouvel objet
@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        type_id = request.form['type_id']
        quantity = request.form['quantity']

        if not name or not type_id or not quantity:
            flash('Tous les champs sont obligatoires !', 'danger')
            return redirect(url_for('add_item'))

        if not quantity.isdigit() or int(quantity) < 0:
            flash('La quantité doit être un nombre positif !', 'danger')
            return redirect(url_for('add_item'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO inventory (name, type_id, quantity) VALUES (?, ?, ?)', (name, type_id, quantity))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Objet ajouté avec succès!', 'success')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM item_types')
    item_types = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('edit_item.html', action='Ajouter', item_types=item_types)


# Route pour consommer un objet
@app.route('/consume/<int:item_id>', methods=['POST'])
def consume_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
    item = cursor.fetchone()

    if item and item['quantity'] > 0:
        new_quantity = item['quantity'] - 1
        cursor.execute('UPDATE inventory SET quantity = ? WHERE id = ?', (new_quantity, item_id))
        conn.commit()
        flash('Objet consommé avec succès !', 'success')
    else:
        flash('Quantité insuffisante !', 'danger')

    cursor.close()
    conn.close()
    return redirect(url_for('index'))


# Route pour supprimer un objet
@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Objet supprimé avec succès !', 'success')
    return redirect(url_for('index'))


@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Récupérer l'élément à modifier
    cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
    item = cursor.fetchone()

    if not item:
        flash('Objet non trouvé !', 'danger')
        return redirect(url_for('index'))

    cursor.execute('SELECT * FROM item_types')
    item_types = cursor.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        type_id = request.form['type_id']
        quantity = request.form['quantity']

        # Validation des champs
        if not name or not type_id or not quantity:
            flash('Tous les champs sont obligatoires !', 'danger')
            return render_template('edit_item.html', action='Modifier', item=item, item_types=item_types)

        # Mise à jour de l'élément
        cursor.execute('UPDATE inventory SET name = ?, type_id = ?, quantity = ? WHERE id = ?',
                       (name, type_id, quantity, item_id))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Objet modifié avec succès !', 'success')
        return redirect(url_for('index'))

    cursor.close()
    conn.close()
    return render_template('edit_item.html', action='Modifier', item=item, item_types=item_types)


# Exécuter l'application Flask
if __name__ == '__main__':
    init_db()  # Créer la base de données et les tables si elles n'existent pas
    app.run(debug=True)


@app.cli.command('init-db')
def init_db_command():
    """Initialise la base de données."""
    init_db()
    click.echo('Base de données initialisée.')
