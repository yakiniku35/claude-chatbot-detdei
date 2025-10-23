import sqlite3

class ConversationDB:
    def __init__(self, db_name='conversations.db'):
        """Initialize the database connection and create tables if they don't exist."""
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        """Create tables for storing conversation data, feedback, and metrics."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                user_input TEXT,
                bot_response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY,
                conversation_id INTEGER,
                rating INTEGER,
                comments TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY,
                total_conversations INTEGER,
                average_rating REAL,
                FOREIGN KEY (id) REFERENCES conversations (id)
            )
        ''')
        self.connection.commit()

    def insert_conversation(self, user_input, bot_response):
        """Insert a new conversation record."""
        self.cursor.execute('''
            INSERT INTO conversations (user_input, bot_response)
            VALUES (?, ?)
        ''', (user_input, bot_response))
        self.connection.commit()

    def insert_feedback(self, conversation_id, rating, comments):
        """Insert feedback for a conversation."""
        self.cursor.execute('''
            INSERT INTO feedback (conversation_id, rating, comments)
            VALUES (?, ?, ?)
        ''', (conversation_id, rating, comments))
        self.connection.commit()

    def get_metrics(self):
        """Retrieve metrics for conversations."""
        self.cursor.execute('''
            SELECT COUNT(*) AS total_conversations, AVG(rating) AS average_rating
            FROM feedback
        ''')
        return self.cursor.fetchone()

    def close(self):
        """Close the database connection."""
        self.connection.close()