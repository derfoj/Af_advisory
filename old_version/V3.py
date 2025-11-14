#qkjWRat6qkqqNXIHnA002hScTmGxittw
import sys
import os
import re
import requests
import pymysql
import warnings
import logging
import pandas as pd
import PyPDF2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTextEdit, QLineEdit, QComboBox, QFileDialog, QMessageBox,
    QTabWidget, QHBoxLayout, QGroupBox, QSplitter, QFrame
)
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from sqlalchemy import create_engine, text


# Import for AI features - optional dependencies
from langchain_community.utilities import SQLDatabase
from langchain_mistralai.chat_models import ChatMistralAI
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from openai import OpenAI
AI_FEATURES_AVAILABLE = True



# Configurer les logs
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
except ImportError:
    MISTRAL_API_KEY = ""

warnings.filterwarnings("ignore")

# Variables globales pour PDF
vector_store = None
client = None


class WorkerThread(QThread):
    """Thread amélioré avec gestion robuste des résultats"""
    finished = pyqtSignal(str, bool)  # message, success
    progress_update = pyqtSignal(str)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._result = (False, "Non initialisé")  # (success, message)

    def run(self):
        try:
            # Exécute la fonction et capture le résultat
            result = self.function(*self.args, **self.kwargs)
            
            # Normalise le résultat en tuple (success, message)
            if result is None:
                self._result = (False, "Aucun résultat retourné")
            elif isinstance(result, bool):
                self._result = (result, "Succès" if result else "Échec")
            elif isinstance(result, tuple):
                self._result = result if len(result) == 2 else (False, str(result))
            else:
                self._result = (True, str(result))
                
        except Exception as e:
            self._result = (False, f"Erreur: {str(e)}")
            logger.exception("Erreur dans WorkerThread")
            
        finally:
            # Émet le signal avec les résultats normalisés
            self.finished.emit(self._result[1], self._result[0])

    def get_result(self):
        """Méthode pour récupérer le résultat après exécution"""
        return self._result
    
class URLImporter:
    """Télécharge un fichier depuis une URL"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.file_path = None

    def download_from_url(self):
        url = self.main_window.url_input.text().strip()
        if not url:
            QMessageBox.warning(self.main_window, "Erreur", "Veuillez entrer une URL valide.")
            return None

        # Vérifier les extensions supportées
        supported_extensions = ['.pdf', '.sql', '.csv', '.xlsx']
        file_ext = os.path.splitext(url)[1].lower()
        
        if file_ext not in supported_extensions:
            QMessageBox.warning(self.main_window, "Type non supporté",
                            f"Seuls ces types sont supportés: {', '.join(supported_extensions)}")
            return None

        file_name = os.path.basename(url)
        save_path = os.path.join(os.getcwd(), file_name)
        self.file_path = save_path

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            self.main_window.status_label.setText(f"✅ Fichier téléchargé depuis l'URL : {save_path}")
            return save_path

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self.main_window, "Erreur de téléchargement", 
                               f"Impossible de télécharger le fichier : {str(e)}")
            return None


class SQLConnectionWindow(QMainWindow):
    """Fenêtre séparée pour la connexion SQL"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion MySQL")
        self.setGeometry(300, 300, 400, 300)
        self.parent = parent
        
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.layout = QVBoxLayout()
        
        # Configuration du groupe de connexion
        connection_group = QGroupBox("Paramètres de connexion")
        connection_layout = QVBoxLayout()
        
        # Champs de saisie
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("localhost")
        connection_layout.addWidget(QLabel("Hôte:"))
        connection_layout.addWidget(self.host_input)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("root")
        connection_layout.addWidget(QLabel("Utilisateur:"))
        connection_layout.addWidget(self.user_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("motdepasse")
        self.password_input.setEchoMode(QLineEdit.Password)
        connection_layout.addWidget(QLabel("Mot de passe:"))
        connection_layout.addWidget(self.password_input)

        self.database_input = QLineEdit()
        self.database_input.setPlaceholderText("(optionnel)")
        connection_layout.addWidget(QLabel("Base de données:"))
        connection_layout.addWidget(self.database_input)
        
        connection_group.setLayout(connection_layout)
        self.layout.addWidget(connection_group)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Se connecter")
        self.connect_button.clicked.connect(self.try_connect)
        button_layout.addWidget(self.connect_button)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)
        
        self.layout.addLayout(button_layout)
        
        # Label de statut
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)
        
        # Charger les paramètres existants s'ils existent
        if hasattr(self.parent, 'sql_host'):
            self.host_input.setText(self.parent.sql_host)
        if hasattr(self.parent, 'sql_user'):
            self.user_input.setText(self.parent.sql_user)
        if hasattr(self.parent, 'sql_database'):
            self.database_input.setText(self.parent.sql_database)
        
        self.centralWidget.setLayout(self.layout)
    
    def try_connect(self):
        """Tente de se connecter à MySQL"""
        host = self.host_input.text().strip() or "localhost"
        user = self.user_input.text().strip() or "root"
        password = self.password_input.text().strip()
        database = self.database_input.text().strip()

        if not all([host, user]):
            self.status_label.setText("❌ Hôte et utilisateur sont obligatoires")
            return

        try:
            
            connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database if database else None,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            auth_plugin='mysql_native_password'
            )
            
            if connection.open:
                self.parent.update_sql_credentials(host, user, password, database)
                self.parent.update_mysql_status(True)
                connection.close()
                self.close()
                QMessageBox.information(self, "Succès", "Connexion à MySQL établie!")
        except pymysql.Error as err:
            self.status_label.setText(f"❌ Erreur: {err}")


class PDFImporter:
    """Classe pour la gestion des PDF"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def extract_text(self, pdf_file_paths):
        """Extraction robuste pour tout type de PDF"""
        full_text = ""
        for path in pdf_file_paths:
            try:
                with open(path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    
                    # Vérification basique du PDF
                    if len(reader.pages) == 0:
                        raise ValueError("PDF vide - aucune page trouvée")
                    
                    # Extraction avec gestion des erreurs par page
                    for i, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                # Nettoyage minimal conservant la structure
                                page_text = re.sub(r'\s+', ' ', page_text).strip()
                                full_text += f"Page {i+1}:\n{page_text}\n\n"
                        except Exception as e:
                            logger.warning(f"Erreur page {i+1}: {str(e)}")
                            continue
                            
            except Exception as e:
                logger.error(f"Erreur fichier {path}: {str(e)}")
                raise ValueError(f"Impossible de lire le PDF: {str(e)}")
        
        if not full_text.strip():
            raise ValueError("Aucun texte extractible - le PDF peut être une image ou protégé")
        
        return full_text
    
    def split_text(self, text, chunk_size=1000, chunk_overlap=100):
        if AI_FEATURES_AVAILABLE:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ".", "!", "?", ",", " "]
            )
            return splitter.split_text(text)
        else:
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-chunk_overlap)]
            
    def create_vector_store(self, chunks):
        if AI_FEATURES_AVAILABLE:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            return FAISS.from_texts(chunks, embeddings)
        else:
            QMessageBox.warning(self.main_window, "Fonctionnalité limitée", 
                               "Les fonctionnalités avancées d'IA ne sont pas disponibles. Installez les dépendances requises.")
            return None
            
    def load_pdf_engine(self, pdf_path):
        global vector_store
        
        try:
            raw_text = self.extract_text([pdf_path])
            chunks = self.split_text(raw_text)
            vector_store = self.create_vector_store(chunks)
            
            # Pas besoin d'initialiser 'client' ici, c'est géré par AIProcessor
            return True, "PDF chargé avec succès"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"

class SQLProcessor:
    """Classe pour traiter les fichiers SQL"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def get_database_name_from_sql(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as sql_file:
                sql_script = sql_file.read()
            
            # Try to find database name in CREATE DATABASE or USE statements
            match_create = re.search(r"CREATE\s+DATABASE\s+(?:IF NOT EXISTS\s+)?`?([a-zA-Z0-9_]+)`?", sql_script, re.IGNORECASE)
            match_use = re.search(r"USE\s+`?([a-zA-Z0-9_]+)`?", sql_script, re.IGNORECASE)
            
            if match_create:
                return match_create.group(1)
            elif match_use:
                return match_use.group(1)
            else:
                # If no database name found, return the default one
                return self.main_window.sql_database or "tempo"
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier SQL : {e}")
            return self.main_window.sql_database or "tempo"
    
    def execute_sql_file(self, file_path, db_name):
        # Vérification initiale
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Fichier introuvable: {file_path}")
            
        if not all([self.main_window.sql_host, self.main_window.sql_user]):
            raise ValueError("Configuration MySQL incomplète")

        # Vérifier la taille du fichier
        file_size = os.path.getsize(file_path)
        
        # Si le fichier est plus grand que 5MB, utiliser la méthode pour les gros fichiers
        if file_size > 5 * 1024 * 1024:  # 5MB
            self.main_window.update_status(f"Fichier SQL volumineux détecté ({file_size / (1024 * 1024):.2f} MB). Utilisation de la méthode optimisée.")
            return self.execute_large_sql_file(file_path, db_name)
        
        # Pour les fichiers plus petits
        try:
            # Lire le contenu du fichier SQL
            with open(file_path, 'r', encoding='utf-8') as sql_file:
                sql_script = sql_file.read()
            
            # Connexion à MySQL
            try:
                connection = pymysql.connect(
                    host=self.main_window.sql_host,
                    user=self.main_window.sql_user,
                    password=self.main_window.sql_password,
                    charset='utf8mb4',
                    connect_timeout=10,
                    cursorclass=pymysql.cursors.DictCursor,
                    auth_plugin='mysql_native_password'
                )
                
                # Créer la base de données si elle n'existe pas
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
                    cursor.execute(f"USE `{db_name}`")
                    
                    # Prétraiter le script SQL
                    sql_script = re.sub(r'/\*.*?\*/', '', sql_script, flags=re.DOTALL)
                    sql_script = re.sub(r'--.*?$', '', sql_script, flags=re.MULTILINE)
                    
                    # Diviser le script en instructions individuelles
                    statements = []
                    
                    # Division basée sur les points-virgules
                    current_statement = ""
                    in_string = False
                    string_delimiter = None
                    
                    for char in sql_script:
                        if char in ["'", '"'] and not in_string:
                            in_string = True
                            string_delimiter = char
                            current_statement += char
                        elif char == string_delimiter and in_string:
                            in_string = False
                            current_statement += char
                        elif char == ';' and not in_string:
                            current_statement += char
                            if current_statement.strip():
                                statements.append(current_statement.strip())
                            current_statement = ""
                        else:
                            current_statement += char
                    
                    # Ajouter la dernière instruction si elle existe
                    if current_statement.strip():
                        statements.append(current_statement.strip())
                    
                    # Exécuter chaque instruction
                    for stmt in statements:
                        if stmt:  # Ignorer les instructions vides
                            try:
                                cursor.execute(stmt)
                            except pymysql.Error as e:
                                self.main_window.update_status(f"Avertissement: Impossible d'exécuter l'instruction: {e}")
                    
                    connection.commit()
                
                connection.close()
                return True
            
            except Exception as e:
                self.main_window.update_status(f"Erreur lors de l'exécution du script SQL : {e}")
                return False
            
        except pymysql.Error as e:
            logger.error(f"Erreur MySQL: {str(e)}")
            raise

    def execute_large_sql_file(self, file_path, db_name):
        try:
            # Connexion à MySQL avec paramètres de timeout augmentés
            connection = pymysql.connect(
                host=self.main_window.sql_host,
                user=self.main_window.sql_user,
                password=self.main_window.sql_password,
                charset='utf8mb4',
                connect_timeout=300,
                read_timeout=300,
                write_timeout=300,
                cursorclass=pymysql.cursors.DictCursor,
                auth_plugin='mysql_native_password'
            )
            
            # Créer la base de données si elle n'existe pas
            with connection.cursor() as cursor:
                cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
                cursor.execute(f"USE `{db_name}`")
                
                # Traiter le fichier SQL par morceaux (chunks)
                chunk_size = 1024 * 1024  # 1MB par morceau
                statement = ""
                
                # Ouvrir le fichier SQL et le lire par morceaux
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as sql_file:
                    while True:
                        chunk = sql_file.read(chunk_size)
                        if not chunk:
                            break
                        
                        # Traiter le morceau actuel
                        lines = chunk.split('\n')
                        
                        # Si c'est le premier morceau ou si le morceau précédent se terminait par un point-virgule
                        if not statement:
                            statement = lines[0]
                        else:
                            statement += lines[0]
                        
                        # Traiter toutes les lignes du morceau sauf la première (déjà traitée)
                        for i in range(1, len(lines)):
                            line = lines[i].strip()
                            
                            # Ignorer les commentaires et les lignes vides
                            if not line or line.startswith('--') or line.startswith('/*'):
                                continue
                                
                            statement += " " + line
                            
                            # Si la ligne se termine par un point-virgule, c'est la fin d'une instruction
                            if line.endswith(';'):
                                try:
                                    # Désactiver les vérifications de clés étrangères pour accélérer les insertions
                                    if statement.strip().upper().startswith("INSERT"):
                                        cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
                                    
                                    cursor.execute(statement)
                                    connection.commit()
                                    
                                    # Réactiver les vérifications de clés étrangères
                                    if statement.strip().upper().startswith("INSERT"):
                                        cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
                                        
                                except pymysql.Error as e:
                                    self.main_window.update_status(f"Avertissement: Impossible d'exécuter l'instruction: {e}")
                                
                                statement = ""
                
                # Traiter la dernière instruction si elle existe et ne se termine pas par un point-virgule
                if statement.strip():
                    try:
                        cursor.execute(statement)
                        connection.commit()
                    except pymysql.Error as e:
                        self.main_window.update_status(f"Avertissement: Impossible d'exécuter l'instruction: {e}")
            
            connection.close()
            return True
        
        except Exception as e:
            self.main_window.update_status(f"Erreur lors de l'exécution du script SQL : {e}")
            return False


class DataProcessor:
    """Classe pour traiter les fichiers de données (CSV, Excel)"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def process_data_file(self, file_path):
        try:
            # Vérification de l'extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Chargement différencié
            if file_ext == '.csv':
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin1')
            elif file_ext == '.xlsx':
                df = pd.read_excel(file_path)
            else:
                return False, "Type de fichier non supporté"

            if df.empty:
                return False, "Le fichier est vide"
                
            # Connexion MySQL
            db_url = f"mysql+pymysql://{self.main_window.sql_user}:{self.main_window.sql_password}@{self.main_window.sql_host}/?auth_plugin=mysql_native_password"
            engine = create_engine(db_url)
            
            db_name = self.main_window.sql_database or "tempo"
            with engine.connect() as conn:
                conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
            
            db_url = f"mysql+pymysql://{self.main_window.sql_user}:{self.main_window.sql_password}@{self.main_window.sql_host}/{db_name}?auth_plugin=mysql_native_password"
            engine = create_engine(db_url)
            
            table_name = os.path.splitext(os.path.basename(file_path))[0].replace(" ", "_")[:64]
            
            # Import avec gestion des erreurs
            try:
                df.to_sql(table_name, engine, index=False, if_exists="replace", chunksize=1000)
                return True, f"Données importées dans la table '{table_name}'"
            except Exception as e:
                return False, f"Erreur lors de l'import: {str(e)}"
                
        except Exception as e:
            logger.error(f"Erreur DataProcessor: {str(e)}")
            return False, f"Erreur majeure: {str(e)}"


class AIProcessor:
    def __init__(self, main_window):
        self.main_window = main_window
        self.client = None
        self.SENSITIVE_KEYWORDS = [
            "diagnostic", "traitement", "posologie", 
            "prescription", "mg", "dosage", "médicament"
        ]

    def is_sensitive_question(self, text):
        """Vérifie si la question contient des mots-clés sensibles"""
        return any(keyword in text.lower() for keyword in self.SENSITIVE_KEYWORDS)

    def init_mistral_client(self):
        """Initialise le client Mistral une seule fois"""
        if not self.client and MISTRAL_API_KEY:
            self.client = OpenAI(api_key=MISTRAL_API_KEY, base_url="https://api.mistral.ai/v1")

    def generate_pdf_answer(self, question):
        global vector_store
        
        if not MISTRAL_API_KEY:
            return "❌ Clé API Mistral manquante. Ajoutez-la dans l'onglet Configuration."
        
        # Initialisation différée du client
        if self.client is None:
            try:
                self.client = OpenAI(api_key=MISTRAL_API_KEY, base_url="https://api.mistral.ai/v1")
            except Exception as e:
                return f"❌ Erreur d'initialisation du client: {str(e)}"
        
        if vector_store is None:
            return "Les fonctionnalités PDF ne sont pas disponibles. Aucun document PDF n'a été chargé."
        
        question_lower = question.lower()

        if any(phrase in question_lower for phrase in [
            "salut", "bonjour", "tu fais quoi", "que fais-tu", "que fais tu", "que fais tu en tant qu'ia",
            "qui es-tu", "c'est quoi ton rôle", "à quoi tu sers", "qu'est-ce que tu fais", "présente toi", "tu es qui",
            "tu es l'ia", "comment tu peux m'aider", "tu es baba"
        ]):
            return (
                "👋 Bonjour ! Je suis un assistant virtuel conçu pour t'aider à analyser des documents PDF et des bases de données SQL.\n\n"
                "📚 Je peux te résumer, t'expliquer, ou t'orienter en cas de besoin.\n"
            )

        if len(question_lower.split()) < 3:
            return "Peux-tu préciser ta question pour que je puisse t'aider efficacement ?"

        if self.is_sensitive_question(question):
            return "Je ne peux pas répondre à cette question. Veuillez consulter un professionnel de santé."

        try:
            results = vector_store.similarity_search_with_score(question, k=5)
            results = [(doc, score) for doc, score in results if score < 1.5]

            if not results:
                return "Je n'ai rien trouvé de pertinent pour ta question dans le document PDF."

            context = "\n".join([doc.page_content for doc, _ in results])
            prompt = f"Voici le contenu extrait du document :\n{context}\n\nQuestion : {question}\nRéponse :"
        except Exception as e:
            logger.error("Erreur pendant la recherche de contexte : %s", e)
            return "Erreur lors de la recherche d'informations dans le PDF."

        try:
            response = self.client.chat.completions.create(
                model="mistral-tiny",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un assistant virtuel bienveillant, spécialisé dans l'analyse de documents. "
                            "Tu réponds de manière claire, précise et rassurante, avec des messages bien structurés.\n\n"
                            "• Utilise des phrases simples et humaines.\n"
                            "• Structure les informations si besoin avec des retours à la ligne, des puces (•), ou des étapes (1, 2, 3...).\n"
                            "• Ne fais jamais de diagnostic médical.\n"
                            "• Guide l'utilisateur comme un assistant efficace."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error("Erreur API Mistral : %s", e)
            return "Erreur lors de la génération de réponse pour le PDF."
    
    def _basic_sql_response(self, question):
        """Réponse de base si l'IA avancée échoue."""
        logger.warning(f"Utilisation de la réponse SQL de base pour la question: {question}")
        return "❌ Une erreur est survenue lors du traitement de la requête SQL. Les fonctionnalités d'IA avancées peuvent être indisponibles."

    def process_sql_query(self, question):
        if not AI_FEATURES_AVAILABLE:
            return self._basic_sql_response(question)
        
        try:
            # Connexion à la base de données
            db_name = self.main_window.sql_database or "tempo"
            db_url = f"mysql+pymysql://{self.main_window.sql_user}:{self.main_window.sql_password}@{self.main_window.sql_host}/{db_name}?auth_plugin=mysql_native_password"
            
            try:
                engine = create_engine(db_url)
                db = SQLDatabase(engine)
            except Exception as e:
                return f"❌ Connexion MySQL échouée: {str(e)}"

            # Configuration du modèle Mistral
            if not MISTRAL_API_KEY:
                return self._basic_sql_response(question)
                
            try:
                llm = ChatMistralAI(
                    model="mistral-large-latest",
                    temperature=0.0,
                    mistral_api_key=MISTRAL_API_KEY
                )
                
                # Génération de la requête SQL
                write_query = create_sql_query_chain(llm, db)
                response = write_query.invoke({"question": f"{question}, n'hésites pas à utiliser des joins."})
                
                # Extraction de la requête SQL
                sql_match = re.search(r"```sql\n(.*?)```", response, re.DOTALL)
                sql_query = sql_match.group(1) if sql_match else response
                
                # Exécution de la requête
                execute_query = QuerySQLDataBaseTool(db=db)
                result = execute_query.invoke({"query": sql_query})
                
                # Formatage de la réponse
                answer_prompt = PromptTemplate.from_template(
                    """A partir de la question utilisateur suivante, la requête SQL correspondante et le résultat SQL, réponds à la question utilisateur.

    Question : {question}
    Requête SQL : {query}
    Résultat SQL : {result}
    Réponse : """
                )
                
                # Chaîne de traitement finale
                answer = answer_prompt | llm | StrOutputParser()
                chain = (
                    RunnablePassthrough.assign(query=lambda x: sql_query).assign(
                        result=lambda x: result
                    )
                    | answer
                )
                
                # Génération de la réponse finale
                final_response = chain.invoke({"question": question})
                
                return f"Réponse:\n{final_response}"

            except Exception as e:
                logger.error(f"Erreur API Mistral: {str(e)}")
                return self._basic_sql_response(question)

        except Exception as e:
            logger.error(f"Erreur lors du traitement de la requête SQL: {e}")
            return f"Une erreur s'est produite lors du traitement de votre requête: {str(e)}"


class ChatbotWindow(QMainWindow):
    """Fenêtre principale du Chatbot"""
    def __init__(self):
        super().__init__()
        # Configurez le logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='app_debug.log'
        )
        self.setWindowTitle("AI DataBot - Assistant de données")
        self.setGeometry(100, 100, 1200, 800)
        
        # Variables SQL
        self.sql_host = "localhost"
        self.sql_user = "root"
        self.sql_password = ""
        self.sql_database = "tempo"
        self.file_path = None
        
        # Initialiser les processeurs
        self.url_importer = URLImporter(self)
        self.sql_processor = SQLProcessor(self)
        self.data_processor = DataProcessor(self)
        self.pdf_importer = PDFImporter(self)
        self.ai_processor = AIProcessor(self)
        
        # Définir une police à espacement fixe pour l'affichage du chat
        self.monospace_font = QFont("Consolas")
        self.monospace_font.setPointSize(9)
        
        self.initUI()
    
    def initUI(self):
        """Initialise l'interface du Chatbot avec des onglets"""
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.main_layout = QVBoxLayout()
        
        # Créer un widget d'onglets
        self.tab_widget = QTabWidget()
        
        # Onglet d'importation de fichiers
        self.import_tab = QWidget()
        self.import_layout = QVBoxLayout()
        self.import_tab.setLayout(self.import_layout)
        
        # Onglet de chat
        self.chat_tab = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_tab.setLayout(self.chat_layout)
        
        # Onglet de configuration
        self.config_tab = QWidget()
        self.config_layout = QVBoxLayout()
        self.config_tab.setLayout(self.config_layout)
        
        # Ajout des onglets au widget d'onglets
        self.tab_widget.addTab(self.import_tab, "Importation de fichiers")
        self.tab_widget.addTab(self.chat_tab, "Chat")
        self.tab_widget.addTab(self.config_tab, "Configuration")
        
        # Ajouter le widget d'onglets au layout principal
        self.main_layout.addWidget(self.tab_widget)
        
        # Initialiser les contenus des onglets
        self.setupImportTab()
        self.setupChatTab()
        self.setupConfigTab()
        
        self.centralWidget.setLayout(self.main_layout)

    def set_ui_interactive(self, enabled):
        """Active/désactive tous les éléments interactifs de l'UI"""
        try:
            widgets = [
                self.download_button,
                self.browse_button,
                self.clear_button,
                self.chat_input,
                self.send_button,
                self.mysql_connect_button
            ]
            
            for widget in widgets:
                widget.setEnabled(enabled)
                
            self.tab_widget.setTabEnabled(1, enabled)  # Onglet Chat
            QApplication.processEvents()
        except Exception as e:
            logger.error(f"Erreur set_ui_interactive: {str(e)}")

    def enable_pdf_features(self, enabled):
        """Active/désactive spécifiquement les fonctionnalités PDF"""
        try:
            if hasattr(self, 'pdf_action_buttons'):
                for btn in self.pdf_action_buttons:
                    btn.setEnabled(enabled)
        except Exception as e:
            logger.error(f"Erreur enable_pdf_features: {str(e)}")

    def setupImportTab(self):
        """Configure l'onglet d'importation de fichiers"""
        # Section URL
        url_group = QGroupBox("Téléchargement depuis URL")
        url_layout = QVBoxLayout()
        
        self.url_label = QLabel("Entrez une URL pour télécharger un fichier:")
        url_layout.addWidget(self.url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Entrez l'URL ici")
        url_layout.addWidget(self.url_input)
        
        self.download_button = QPushButton("Télécharger depuis URL")
        self.download_button.clicked.connect(self.import_url)
        url_layout.addWidget(self.download_button)
        
        url_group.setLayout(url_layout)
        self.import_layout.addWidget(url_group)
        
        # Section Fichier local
        file_group = QGroupBox("Importation de fichier local")
        file_layout = QVBoxLayout()
        
        self.db_label = QLabel("Type de fichier:")
        file_layout.addWidget(self.db_label)
        
        self.db_combo = QComboBox()
        self.db_combo.addItems(["CSV", "XLSX", "PDF", "SQL", "Oracle"])
        file_layout.addWidget(self.db_combo)
        
        self.browse_button = QPushButton("Parcourir")
        self.browse_button.clicked.connect(self.browse_database)
        file_layout.addWidget(self.browse_button)
        
        self.clear_button = QPushButton("Décharger le fichier")
        self.clear_button.clicked.connect(self.clear_loaded_file)
        file_layout.addWidget(self.clear_button)
        
        file_group.setLayout(file_layout)
        self.import_layout.addWidget(file_group)
        
        # Section Statut
        self.status_label = QLabel("Aucun fichier chargé.")
        self.import_layout.addWidget(self.status_label)
        
        # Section MySQL
        mysql_group = QGroupBox("Connexion MySQL")
        mysql_layout = QVBoxLayout()
        
        self.mysql_connect_button = QPushButton("Connexion MySQL")
        self.mysql_connect_button.clicked.connect(self.open_sql_connection_dialog)
        mysql_layout.addWidget(self.mysql_connect_button)
        
        self.mysql_status_label = QLabel("❌ Non connecté à MySQL")
        mysql_layout.addWidget(self.mysql_status_label)
        
        mysql_group.setLayout(mysql_layout)
        self.import_layout.addWidget(mysql_group)
        
        # Ajouter un espace extensible
        self.import_layout.addStretch()
    
    def setupChatTab(self):
        """Configure l'onglet de chat"""
        # Créer un séparateur pour diviser l'espace
        splitter = QSplitter(Qt.Vertical)
        
        # Section d'affichage du chat
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(self.monospace_font)
        splitter.addWidget(self.chat_display)
        
        # Section de saisie
        input_frame = QFrame()
        input_layout = QVBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Tapez votre message...")
        self.chat_input.returnPressed.connect(self.chatbot_response)
        input_layout.addWidget(self.chat_input)
        
        self.send_button = QPushButton("Envoyer")
        self.send_button.clicked.connect(self.chatbot_response)
        input_layout.addWidget(self.send_button)
        
        input_frame.setLayout(input_layout)
        splitter.addWidget(input_frame)
        
        # Configurer les tailles des sections
        splitter.setSizes([600, 100])
        
        self.chat_layout.addWidget(splitter)
    
    def setupConfigTab(self):
        """Configure l'onglet de configuration"""
        # Section API
        api_group = QGroupBox("Configuration API")
        api_layout = QVBoxLayout()
        
        self.api_label = QLabel("Clé API Mistral (optionnel):")
        api_layout.addWidget(self.api_label)
        
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Entrez votre clé API Mistral ici")
        self.api_input.setText(MISTRAL_API_KEY)
        api_layout.addWidget(self.api_input)
        
        self.save_api_button = QPushButton("Enregistrer")
        self.save_api_button.clicked.connect(self.save_api_key)
        api_layout.addWidget(self.save_api_button)
        
        api_group.setLayout(api_layout)
        self.config_layout.addWidget(api_group)
        
        # Section A propos
        about_group = QGroupBox("À propos")
        about_layout = QVBoxLayout()
        
        about_text = QLabel(
            "AI DataBot v1.0\n\n"
            "Un assistant intelligent pour analyser vos données:\n"
            "- Fichiers CSV/Excel\n"
            "- Bases de données SQL\n"
            "- Documents PDF\n\n"
            "© 2025 - Développé avec PyQt5"
        )
        about_text.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_text)
        
        about_group.setLayout(about_layout)
        self.config_layout.addWidget(about_group)
        
        # Ajouter un espace extensible
        self.config_layout.addStretch()
    
    def save_api_key(self):
        """Enregistre la clé API Mistral"""
        global MISTRAL_API_KEY
        MISTRAL_API_KEY = self.api_input.text().strip()
        QMessageBox.information(self, "Succès", "Clé API enregistrée (pour cette session)")
    
    def open_sql_connection_dialog(self):
        """Ouvre la fenêtre de connexion SQL séparée"""
        self.sql_window = SQLConnectionWindow(self)
        self.sql_window.show()
    
    def update_sql_credentials(self, host, user, password, database=None):
        """Met à jour les identifiants SQL"""
        self.sql_host = host
        self.sql_user = user
        self.sql_password = password
        if database:
            self.sql_database = database
    
    def update_mysql_status(self, connected):
        """Affiche le statut MySQL"""
        try:
            if connected:
                db_info = self.sql_database if self.sql_database else "aucune base sélectionnée"
                self.mysql_status_label.setText(
                    f"✅ Connecté à MySQL (Host: {self.sql_host}, DB: {db_info})"
                )
            else:
                self.mysql_status_label.setText("❌ Non connecté à MySQL")
        except Exception as e:
            logger.error(f"Erreur update_mysql_status: {str(e)}")
            self.mysql_status_label.setText("❌ Erreur statut MySQL")
    
    def update_status(self, message):
        """Met à jour le label de statut"""
        self.status_label.setText(message)
        self.status_label.repaint()
    
    def clear_loaded_file(self):
        """Décharge le fichier actuellement chargé"""
        self.url_input.clear()
        self.status_label.setText("Aucun fichier chargé.")
        self.file_path = None
    
    def browse_database(self):
        try:
            selected_type = self.db_combo.currentText()
            file_filters = {
                "CSV": "Fichiers CSV (*.csv)",
                "XLSX": "Fichiers Excel (*.xlsx)",
                "PDF": "Fichiers PDF (*.pdf)",
                "SQL": "Fichiers SQL (*.sql)",
                "Oracle": "Fichiers Oracle (*.dmp)"
            }
            
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Sélectionner un fichier", "", file_filters.get(selected_type, "Tous les fichiers (*.*)"))
            
            if not file_name:
                return

            self.file_path = file_name


            if selected_type == "PDF":
                self._handle_pdf(file_name)
            elif selected_type in ["CSV", "XLSX"]:
                self._handle_data_file(file_name)
            elif selected_type == "SQL":
                self._handle_sql(file_name)

            self.status_label.setText(f"✅ Fichier chargé: {file_name}")
            QApplication.processEvents()  # Force l'update de l'interface
        except Exception as e:
            logger.error(f"Erreur browse_database: {str(e)}")
            self.status_label.setText(f"❌ Erreur: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le fichier:\n{str(e)}")

    def _handle_pdf(self, file_path):
        """Charge un PDF avec gestion d'erreur améliorée"""
        try:
            if not hasattr(self, 'set_ui_interactive'):
                raise AttributeError("Fonctionnalité manquante: set_ui_interactive")
                
            self.set_ui_interactive(False)
            self.update_status("Chargement du PDF en cours...")
            
            # Initialise les boutons PDF si nécessaire
            if not hasattr(self, 'pdf_action_buttons'):
                self.pdf_action_buttons = [
                    self.send_button,
                    # Ajoutez ici d'autres boutons liés aux PDF
                ]
                
            self.pdf_worker = WorkerThread(self.pdf_importer.load_pdf_engine, file_path)
            self.pdf_worker.finished.connect(self.on_pdf_loaded)
            self.pdf_worker.start()
            
        except Exception as e:
            self.set_ui_interactive(True)
            self.update_status(f"❌ Erreur initiale: {str(e)}")
            QMessageBox.critical(self, "Erreur PDF", f"Échec du chargement:\n{str(e)}")

    def on_pdf_loaded(self, message, success):
        """Callback après chargement du PDF"""
        try:
            # Réactive l'interface
            self.set_ui_interactive(True)
            
            if success:
                self.update_status(f"✅ {message}")
                # Active les fonctionnalités PDF
                self.enable_pdf_features(True)
            else:
                self.update_status(f"❌ {message}")
                QMessageBox.warning(self, "Avertissement PDF", message)
                # Désactive les fonctionnalités PDF
                self.enable_pdf_features(False)
                
        except Exception as e:
            logger.error(f"Erreur dans on_pdf_loaded: {e}")
            self.update_status("❌ Erreur critique lors du traitement")

    def _handle_data_file(self, file_path):
        try:
            # Traitement immédiat sans thread pour mieux capturer les erreurs
            success, message = self.data_processor.process_data_file(file_path)
            self.update_status(message)
            if not success:
                QMessageBox.warning(self, "Avertissement", message)
        except Exception as e:
            logger.error(f"Erreur traitement données: {str(e)}")
            self.update_status(f"❌ Erreur: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur traitement:\n{str(e)}")

    def _handle_sql(self, file_path):
        """Gestion robuste des fichiers SQL"""
        try:
            # Vérification préalable
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Fichier {file_path} introuvable")
                
            if not all([self.sql_host, self.sql_user]):
                raise ValueError("Configuration MySQL incomplète")

            # Désactive le bouton pendant le traitement
            self.browse_button.setEnabled(False)
            self.status_label.setText("Traitement SQL en cours...")
            QApplication.processEvents()

            # Exécution synchrone pour mieux capturer les erreurs
            db_name = self.sql_processor.get_database_name_from_sql(file_path)

            success = self.sql_processor.execute_sql_file(file_path, db_name)
            
            if success:
                msg = f"Script SQL exécuté dans la base '{db_name}'"
                self.sql_database = db_name
                self.status_label.setText(f"✅ {msg}")
            else:
                raise Exception("Échec de l'exécution du script SQL")
                
        except Exception as e:
            msg = f"❌ Erreur SQL: {str(e)}"
            logger.error(msg)
            self.status_label.setText(msg)
            QMessageBox.critical(self, "Erreur SQL", msg)
        finally:
            self.browse_button.setEnabled(True)

    def _on_sql_processed(self, message, success):
        """Callback après traitement SQL"""
        self.update_status(message)
        if not success:
            QMessageBox.warning(self, "Erreur SQL", message)

    def _process_sql_file(self, file_path):
        """Traitement des fichiers SQL"""
        try:
            db_name = self.sql_processor.get_database_name_from_sql(file_path)
            if self.sql_processor.execute_sql_file(file_path, db_name):
                return "Script SQL exécuté avec succès", True
            return "Erreur lors de l'exécution du script SQL", False
        except Exception as e:
            error_msg = f"Erreur traitement SQL: {str(e)}"
            logger.error(error_msg)
            return error_msg, False
        
    def import_url(self):
        """Télécharge un fichier depuis une URL"""
        file_path = self.url_importer.download_from_url()
        if file_path:
            self.file_path = file_path
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Mettre à jour la combobox en fonction du type de fichier
            if file_ext == '.pdf':
                self.db_combo.setCurrentText("PDF")
                self._handle_pdf(file_path)
            elif file_ext == '.sql':
                self.db_combo.setCurrentText("SQL")
                self._handle_sql(file_path)
            elif file_ext in ['.csv', '.xlsx']:
                self.db_combo.setCurrentText("CSV" if file_ext == '.csv' else "XLSX")
                self._handle_data_file(file_path)
            else:
                QMessageBox.warning(self, "Type non supporté", 
                                "Le type de fichier n'est pas supporté")
  
    def chatbot_response(self):
        """Gère les réponses du chatbot"""
        user_input = self.chat_input.text().strip()
        if not user_input:
            return
        
        self.chat_display.append(f"Vous: {user_input}")
        
        # Réponses de base
        if "bonjour" in user_input.lower():
            response = "Bonjour! Comment puis-je vous aider?"
        elif "fichier" in user_input.lower() and self.file_path:
            response = f"Fichier actuel: {self.file_path}"
        elif "mysql" in user_input.lower() and self.sql_host:
            response = f"Connecté à MySQL - Host: {self.sql_host}, User: {self.sql_user}"
        else:
            try:
                if not self.file_path:
                    response = "Veuillez d'abord charger un fichier"
                else:
                    selected_type = self.db_combo.currentText()
                    
                    if selected_type == "PDF":
                        response = self.ai_processor.generate_pdf_answer(user_input)
                    elif selected_type == "SQL":
                        # Vérification supplémentaire pour SQL
                        if not all([self.sql_host, self.sql_user]):
                            response = "Configuration MySQL requise pour les requêtes SQL"
                        else:
                            response = self.ai_processor.process_sql_query(user_input)
                    elif selected_type in ["CSV", "XLSX"]:
                        response = self.ai_processor.process_sql_query(user_input)
                    else:
                        response = "Type de fichier non supporté"
            except Exception as e:
                response = f"❌ Erreur: {str(e)}"
                logger.error(f"Erreur chatbot_response: {str(e)}")
        self.chat_display.append(f"Chatbot: {response}\n")
        self.chat_input.clear()
        
        # Faire défiler vers le bas
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatbotWindow()
    window.show()
    sys.exit(app.exec_())