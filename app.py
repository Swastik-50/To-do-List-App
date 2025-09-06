import streamlit as st
import sqlite3
import hashlib

# ---------------------------
# Database Functions
# ---------------------------
def init_db():
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)''')
    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  task TEXT NOT NULL,
                  done BOOLEAN NOT NULL DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, hash_password(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True

def login_user(username, password):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def add_task(user_id, task):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, task, done) VALUES (?, ?, ?)",
              (user_id, task, False))
    if not c.fetchone():  # Add only if not duplicate
        c.execute("INSERT INTO tasks (user_id, task, done) VALUES (?, ?, ?)",
                  (user_id, task, False))
    conn.commit()
    conn.close()

def get_tasks(user_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def update_task(task_id, done):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = ? WHERE id = ?", (done, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def clear_tasks(user_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ---------------------------
# Streamlit App
# ---------------------------
st.set_page_config(page_title="To-Do List App", page_icon="📝", layout="centered")
st.title("📝 Multi-User To-Do List App")

# Initialize DB
init_db()

# ---------------------------
# Login / Signup
# ---------------------------
if "user" not in st.session_state:
    st.session_state.user = None

menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Menu", menu)

if st.session_state.user is None:
    if choice == "Login":
        st.subheader("Login to your account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user = {"id": user[0], "username": user[1]}
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    elif choice == "Sign Up":
        st.subheader("Create a new account")
        username = st.text_input("Choose a Username")
        password = st.text_input("Choose a Password", type="password")
        if st.button("Sign Up"):
            if add_user(username, password):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists, choose another.")
else:
    # ---------------------------
    # To-Do List Section
    # ---------------------------
    st.sidebar.success(f"Logged in as {st.session_state.user['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    st.subheader(f"{st.session_state.user['username']}'s To-Do List")

    # Add new task
    new_task = st.text_input("Add a new task")
    if st.button("➕ Add Task"):
        if new_task.strip() != "":
            add_task(st.session_state.user["id"], new_task)
            st.success(f"Task '{new_task}' added!")
            st.session_state.new_task = ""
            st.rerun()
        else:
            st.warning("Please enter a task before adding.")

    st.divider()

    # Display tasks
    tasks = get_tasks(st.session_state.user["id"])
    if tasks:
        for task_id, user_id, task, done in tasks:
            cols = st.columns([0.1, 0.7, 0.2])

            # Checkbox for completion
            if cols[0].checkbox("", value=done, key=f"done_{task_id}"):
                update_task(task_id, True)
            else:
                update_task(task_id, False)

            # Task display
            task_style = f"✅ ~~{task}~~" if done else task
            cols[1].write(task_style)

            # Delete button
            if cols[2].button("🗑️ Delete", key=f"delete_{task_id}"):
                delete_task(task_id)
                st.rerun()
    else:
        st.info("No tasks yet. Add one above!")

    # Clear all button
    if tasks:
        if st.button("🧹 Clear All"):
            clear_tasks(st.session_state.user["id"])
            st.success("All tasks cleared!")
            st.rerun()
