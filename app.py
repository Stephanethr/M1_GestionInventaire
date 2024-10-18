from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Créer une instance de l'application Flask
app = Flask(__name__)
# Définir la clé secrète pour les sessions
app.secret_key = os.getenv('SECRET_KEY')

# Configuration de la connexion à la base de données MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

# Initialisation de l'extension MySQL
mysql = MySQL(app)

# Route principale : affichage de l'inventaire
@app.route('/')
def index():
    # Ouvrir un curseur pour interagir avec la base de données
    cursor = mysql.connection.cursor(DictCursor)  # Utiliser DictCursor pour obtenir des résultats sous forme de dictionnaire
    # Exécuter la requête SQL pour récupérer les objets de l'inventaire avec leurs types
    cursor.execute(''' 
        SELECT inventory.id AS item_id, 
               inventory.name AS item_name, 
               item_types.type_name AS item_type, 
               inventory.quantity AS item_quantity 
        FROM inventory 
        JOIN item_types ON inventory.type_id = item_types.id
    ''')
    # Récupérer tous les résultats
    items = cursor.fetchall()
    # Fermer le curseur
    cursor.close()
    # Rendre le template avec les objets récupérés
    return render_template('inventory.html', items=items)

# Route pour ajouter un nouvel objet
@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        name = request.form['name']
        type_id = request.form['type_id']
        quantity = request.form['quantity']

        # Validation des champs obligatoires
        if not name or not type_id or not quantity:
            flash('Tous les champs sont obligatoires!', 'danger')
            return redirect(url_for('add_item'))
        
        # Validation de la quantité
        if not quantity.isdigit() or int(quantity) < 0:
            flash('La quantité doit être un nombre positif!', 'danger')
            return redirect(url_for('add_item'))
        
        # Validation du type d'objet
        if not type_id.isdigit() or int(type_id) < 1:
            flash('Type d\'objet invalide!', 'danger')
            return redirect(url_for('add_item'))
        
        # Ouvrir un curseur pour ajouter l'objet à la base de données
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO inventory (name, type_id, quantity) VALUES (%s, %s, %s)', (name, type_id, quantity))
        mysql.connection.commit()  # Valider la transaction
        cursor.close()
        
        flash('Objet ajouté avec succès!', 'success')  # Message de succès
        return redirect(url_for('index'))  # Rediriger vers la page d'inventaire

    # Si la méthode est GET, récupérer les types d'objets
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute('SELECT * FROM item_types')
    item_types = cursor.fetchall()  # Récupérer tous les types d'objets
    cursor.close()
    
    # Rendre le template d'ajout avec les types d'objets
    return render_template('edit_item.html', action='Ajouter', item_types=item_types)

# Route pour modifier un objet existant
@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    cursor = mysql.connection.cursor(DictCursor)  # Utiliser DictCursor ici
    
    # Récupérer l'objet à modifier
    cursor.execute('SELECT * FROM inventory WHERE id = %s', (item_id,))
    item = cursor.fetchone()  # Récupérer un seul objet
    
    # Récupérer les types d'objets
    cursor.execute('SELECT * FROM item_types')
    item_types = cursor.fetchall()  # Récupérer tous les types d'objets
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        name = request.form['name']
        type_id = request.form['type_id']
        quantity = request.form['quantity']

        # Validation des champs obligatoires
        if not name or not type_id or not quantity:
            flash('Tous les champs sont obligatoires!', 'danger')
            # Rendre le template avec les données de l'objet et les types
            return render_template('edit_item.html', action='Modifier', item=item, item_types=item_types)
        
        # Validation de la quantité
        if not quantity.isdigit() or int(quantity) < 0:
            flash('La quantité doit être un nombre positif!', 'danger')
            return render_template('edit_item.html', action='Modifier', item=item, item_types=item_types)
        
        # Validation du type d'objet
        if not type_id.isdigit() or int(type_id) < 1:
            flash('Type d\'objet invalide!', 'danger')
            return render_template('edit_item.html', action='Modifier', item=item, item_types=item_types)
        
        # Mettre à jour l'objet dans la base de données
        cursor.execute('UPDATE inventory SET name = %s, type_id = %s, quantity = %s WHERE id = %s', 
                       (name, type_id, quantity, item_id))
        mysql.connection.commit()  # Valider la transaction
        cursor.close()
        
        flash('Objet modifié avec succès!', 'success')  # Message de succès
        return redirect(url_for('index'))  # Rediriger vers la page d'inventaire
    
    cursor.close()  # Fermer le curseur
    # Rendre le template d'édition avec les données de l'objet
    return render_template('edit_item.html', action='Modifier', item=item, item_types=item_types)

# Route pour supprimer un objet
@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    cursor = mysql.connection.cursor()  # Ouvrir un curseur
    cursor.execute('DELETE FROM inventory WHERE id = %s', (item_id,))  # Exécuter la requête de suppression
    mysql.connection.commit()  # Valider la transaction
    cursor.close()
    
    flash('Objet supprimé avec succès!', 'success')  # Message de succès
    return redirect(url_for('index'))  # Rediriger vers la page d'inventaire

# Route pour consommer un objet
@app.route('/consume/<int:item_id>', methods=['POST'])
def consume_item(item_id):
    cursor = mysql.connection.cursor(DictCursor)
    
    # Récupérer l'objet à consommer
    cursor.execute('SELECT * FROM inventory WHERE id = %s', (item_id,))
    item = cursor.fetchone()  # Récupérer un seul objet
    
    # Vérifier si l'objet existe et si la quantité est suffisante
    if item and item['quantity'] > 0:
        new_quantity = item['quantity'] - 1  # Décrémenter la quantité
        cursor.execute('UPDATE inventory SET quantity = %s WHERE id = %s', (new_quantity, item_id))
        mysql.connection.commit()  # Valider la transaction
        flash('Objet consommé avec succès!', 'success')  # Message de succès
    else:
        flash('Quantité insuffisante !', 'danger')  # Message d'erreur si la quantité est insuffisante
    
    cursor.close()  # Fermer le curseur
    return redirect(url_for('index'))  # Rediriger vers la page d'inventaire

# Exécuter l'application Flask
if __name__ == '__main__':
    app.run(debug=True)  # Lancer l'application en mode débogage
