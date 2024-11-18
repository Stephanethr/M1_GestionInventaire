import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from init_db import get_db_connection

# Charger les variables d'environnement
load_dotenv()

# Initialiser l'application Flask
app = Flask(__name__)

# Charger la clé secrète depuis le fichier .env pour sécuriser les sessions
app.secret_key = os.getenv('SECRET_KEY')

# Initialiser Bcrypt pour le hachage des mots de passe
bcrypt = Bcrypt(app)

# Route pour la page d'accueil (affiche des informations sur l'utilisateur connecté)
@app.route('/')
def home():
    # Vérifie si l'utilisateur est connecté
    if 'loggedin' in session:
        # Rediriger vers la page d'inventaire si l'utilisateur est connecté
        return redirect(url_for('inventory'))
    else:
        flash("Veuillez vous connecter.", 'info')
        return redirect(url_for('login'))

# Route pour se connecter
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Vérifier les champs obligatoires
        if not email or not password:
            flash('Tous les champs sont obligatoires !', 'danger')
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE user_mail = ?', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        # Vérifier si l'utilisateur existe et si le mot de passe est correct
        if user and bcrypt.check_password_hash(user['user_password'], password):
            session['loggedin'] = True
            session['user_id'] = user['user_id']
            session['username'] = user['user_login']
            flash('Connexion réussie!', 'success')
            # Rediriger directement vers l'inventaire après connexion
            return redirect(url_for('inventory'))
        else:
            flash('Email ou mot de passe incorrect !', 'danger')

    return render_template('login.html')

# Route pour s'inscrire
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        recheck_password = request.form['recheck_password']

        # Vérifier les champs obligatoires
        if not email or not username or not password or not recheck_password:
            flash('Tous les champs sont obligatoires !', 'danger')
            return redirect(url_for('register'))

        # Vérifier si les mots de passe correspondent
        if password != recheck_password:
            flash('Les mots de passe ne correspondent pas !', 'danger')
            return redirect(url_for('register'))

        # Hacher le mot de passe
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()
        # Vérifier si l'email est déjà utilisé
        cursor.execute('SELECT * FROM user WHERE user_mail = ?', (email,))
        account = cursor.fetchone()

        if account:
            flash('Cet email est déjà utilisé!', 'danger')
        else:
            # Insérer le nouvel utilisateur dans la base de données
            cursor.execute(
                'INSERT INTO user (user_login, user_password, user_mail) VALUES (?, ?, ?)',
                (username, hashed_password, email)
            )
            conn.commit()
            session['loggedin'] = True
            session['user_id'] = cursor.lastrowid
            session['username'] = username
            flash('Compte créé avec succès !', 'success')
            return redirect(url_for('home'))

        cursor.close()
        conn.close()

    return render_template('register.html')

# Route pour se déconnecter
@app.route('/logout', methods=['POST'])
def logout():
    # Supprimer toutes les données de session pour déconnecter l'utilisateur
    session.clear()
    flash('Vous avez été déconnecté !', 'success')
    return redirect(url_for('login'))


# Route pour afficher l'inventaire de l'utilisateur connecté
@app.route('/inventory')
def inventory():
    # Vérifier si l'utilisateur est connecté
    if 'loggedin' not in session:
        flash('Veuillez vous connecter pour accéder à votre inventaire.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Récupérer les informations de l'utilisateur connecté
    cursor.execute('SELECT user_login FROM user WHERE user_id = ?', (session['user_id'],))
    user = cursor.fetchone()
    username = user['user_login'] if user else 'Utilisateur'

    # Récupérer les items de l'inventaire de l'utilisateur connecté
    cursor.execute('''
        SELECT inventory.id AS item_id, inventory.name AS item_name, 
               item_types.type_name AS item_type, inventory.quantity AS item_quantity 
        FROM inventory 
        JOIN item_types ON inventory.type_id = item_types.id 
        WHERE inventory.user_id = ?
    ''', (session['user_id'],))
    items = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('inventory.html', items=items, username=username)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if 'loggedin' not in session:
        flash('Veuillez vous connecter pour ajouter un item.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Récupérer les types d'objets pour le sélecteur
    cursor.execute('SELECT * FROM item_types')
    item_types = cursor.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        type_id = request.form['type_id']
        quantity = request.form['quantity']

        if not name or not type_id or not quantity:
            flash('Tous les champs sont obligatoires !', 'danger')
            return redirect(url_for('add_item'))

        # Insérer le nouvel item dans la base de données
        cursor.execute('INSERT INTO inventory (user_id, name, type_id, quantity) VALUES (?, ?, ?, ?)',
                       (session['user_id'], name, type_id, quantity))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Objet ajouté avec succès !', 'success')
        return redirect(url_for('inventory'))

    cursor.close()
    conn.close()
    return render_template('edit_item.html', action='Ajouter', item=None, item_types=item_types)


@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    if 'loggedin' not in session:
        flash('Veuillez vous connecter.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Supprimer l'objet avec l'ID donné
    cursor.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Objet supprimé avec succès !', 'success')
    return redirect(url_for('inventory'))


@app.route('/consume/<int:item_id>', methods=['POST'])
def consume_item(item_id):
    if 'loggedin' not in session:
        flash('Veuillez vous connecter.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Récupérer l'item pour vérifier s'il existe
    cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
    item = cursor.fetchone()

    # Vérifier si l'item existe et si la quantité est suffisante
    if item and item['quantity'] > 0:
        new_quantity = item['quantity'] - 1
        cursor.execute('UPDATE inventory SET quantity = ? WHERE id = ?', (new_quantity, item_id))
        conn.commit()
        flash('Objet consommé avec succès !', 'success')
    else:
        flash('Quantité insuffisante ou objet non trouvé.', 'danger')

    cursor.close()
    conn.close()
    return redirect(url_for('inventory'))

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if 'loggedin' not in session:
        flash('Veuillez vous connecter pour modifier un item.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Récupérer les informations de l'item à modifier
    cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
    item = cursor.fetchone()

    if not item:
        flash("L'objet n'existe pas.", 'danger')
        return redirect(url_for('inventory'))

    # Récupérer les types d'objets pour le sélecteur
    cursor.execute('SELECT * FROM item_types')
    item_types = cursor.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        type_id = request.form['type_id']
        quantity = request.form['quantity']

        if not name or not type_id or not quantity:
            flash('Tous les champs sont obligatoires !', 'danger')
            return redirect(url_for('edit_item', item_id=item_id))

        # Mettre à jour l'item dans la base de données
        cursor.execute('UPDATE inventory SET name = ?, type_id = ?, quantity = ? WHERE id = ?',
                       (name, type_id, quantity, item_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Objet modifié avec succès !', 'success')
        return redirect(url_for('inventory'))

    cursor.close()
    conn.close()
    return render_template('edit_item.html', action='Modifier', item=item, item_types=item_types)

# Lancer l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
