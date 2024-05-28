import mysql.connector
import csv
import random

# Database Configuration
db_config = {
    'user': 'root',
    'password': 'beyourself',
    'host': 'localhost',
    'database': 'expense_splitter',
}

# Initialize the database
def init_db():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("CREATE DATABASE IF NOT EXISTS expense_splitter")
    cursor.execute("USE expense_splitter")

    cursor.execute('''CREATE TABLE IF NOT EXISTS user (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL UNIQUE,
        username VARCHAR(64) NOT NULL UNIQUE,
        password VARCHAR(64) NOT NULL
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS expense (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        description VARCHAR(140),
        amount FLOAT NOT NULL
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS participant (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        expense_id INT,
        amount_owed FLOAT,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (expense_id) REFERENCES expense(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS commodity (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(64) NOT NULL UNIQUE,
        price FLOAT NOT NULL,
        gst_rate FLOAT NOT NULL
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS bill (
        id INT AUTO_INCREMENT PRIMARY KEY,
        total_amount FLOAT NOT NULL,
        gst_amount FLOAT NOT NULL
    )''')

    conn.commit()
    cursor.close()
    conn.close()

# Generate a random 6-digit user ID
def generate_user_id():
    return random.randint(100000, 999999)

# Add a new user to the database
def create_user(username, password):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Generate a unique user ID
    user_id = generate_user_id()
    while check_user_id_existence(user_id):
        user_id = generate_user_id()

    cursor.execute("INSERT INTO user (user_id, username, password) VALUES (%s, %s, %s)", (user_id, username, password))
    conn.commit()
    cursor.close()
    conn.close()

# Check if user ID already exists in the database
def check_user_id_existence(user_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result is not None

# Create a new expense and split it among participants
def create_expense(user_id, description, amount):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO expense (user_id, description, amount) VALUES (%s, %s, %s)", (user_id, description, amount))
    expense_id = cursor.lastrowid

    participants = []
    while True:
        participant = input("Enter participant name (or type 'done' to finish): ")
        if participant.lower() == 'done':
            break
        participants.append(participant)

    split_amount = amount / len(participants)

    for participant_name in participants:
        cursor.execute("SELECT id FROM user WHERE username = %s", (participant_name,))
        participant_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO participant (user_id, expense_id, amount_owed) VALUES (%s, %s, %s)", (participant_id, expense_id, split_amount))

    conn.commit()
    cursor.close()
    conn.close()

# Retrieve a user's expenses from the database
def get_user_expenses(user_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if user:
        cursor.execute("SELECT * FROM expense WHERE user_id = %s", (user_id,))
        expenses = cursor.fetchall()
        print("User not found")
        return
    else:
        print("User not found")
        return

    result = []
    for expense in expenses:
        cursor.execute("SELECT username, amount_owed FROM participant JOIN user ON participant.user_id = user.id WHERE expense_id = %s", (expense[0],))
        participants_data = cursor.fetchall()
        result.append({'description': expense[2], 'amount': expense[3], 'participants': participants_data})

    cursor.close()
    conn.close()

    return result

# Get commodity GST rate by name
def get_commodity_gst(name):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT gst_rate FROM commodity WHERE name = %s", (name,))
    gst_rate = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return gst_rate

# Calculate total amount including GST
def calculate_total_amount(name, quantity):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT price FROM commodity WHERE name = %s", (name,))
    price = cursor.fetchone()[0]

    gst_rate = get_commodity_gst(name)
    total_amount = price * quantity * (1 + gst_rate / 100)

    cursor.close()
    conn.close()

    return total_amount
def validate_user(username, password):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user WHERE username = %s AND password = %s", (username, password))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result is not None


# Initialize the database
init_db()

# Example usage with user input
def main():
    print("Welcome to Expense Splitter!")

    while True:
        print("\nSelect an option:")
        print("1. Create User")
        print("2. Create Expense")
        print("3. Retrieve User Expenses")
        print("4. Calculate Bill")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            user_id=generate_user_id()
            print("Your user id is",user_id)
            create_user(username, password)
            print("User created successfully!")
        elif choice == '2':
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            # Validate user credentials
            if validate_user(username, password):
                user_id=int(input("Enter your user_id:"))
                description = input("Enter expense description: ")
                amount1=float(input("Enter expense amount: "))
                create_expense(user_id,description,amount1)
                print("Expense created successfully!")
            else:
                print("Invalid username or password. Please try again.")
        elif choice == '3':
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            # Validate user credentials
            if validate_user(username, password):
                user_id=int(input("Enter your user id:"))
                user_expenses = get_user_expenses(user_id)
                print("User expenses:")
                for expense in user_expenses:
                    print("Description:", expense['description'])
                    print("Amount:", expense['amount'])
                    print("Participants:")
                    for participant in expense['participants']:
                        print(participant[0], "-", participant[1])
                    print()
            else:
                print("Invalid username or password. Please try again.")
        elif choice == '4':
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            # Validate user credentials
            if validate_user(username, password):
                description = input("Enter commodity name: ")
                quantity = float(input("Enter quantity: "))
                total_amount = calculate_total_amount(description, quantity)
                print("Total amount including GST:", total_amount)
            else:
                print("Invalid username or password. Please try again.")
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please select again.")

if __name__ == "__main__":
    main()

