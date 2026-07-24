from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import bcrypt
import os

from dotenv import load_dotenv

load_dotenv()

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        autocommit=True
    )

app = Flask(__name__)
CORS(app)

print("USING NEW APP.PY")
print("get_db =", get_db)


# HELPER FUNCTIONS
def add_notification(email, title):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO notifications
        (
            email,
            title
        )
        VALUES(%s,%s)
    """,
    (
        email,
        title
    ))
    db.commit()


def add_activity(email, description):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO activity
        (
            email,
            description
        )
        VALUES(%s,%s)
    """,
    (
        email,
        description
    ))

    db.commit()


# REGISTRATION API
@app.route('/register', methods=['POST'])
def register():

    db = get_db()
    cursor = db.cursor()

    data = request.json

    name = data["name"]
    email = data["email"]
    password = data["password"]
    role = data["role"]

    # Check existing user
    cursor.execute(
        "SELECT * FROM users WHERE email=%s",
        (email,)
    )

    """cursor.execute(
        "SELECT id FROM users WHERE email=%s",
        (email,)
    )"""

    existing = cursor.fetchone()

    if existing:
        return jsonify({
            "message": "User Already Exists"
        }), 400

    # Encrypt password
    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )

    cursor.execute(
        """
        INSERT INTO users
        (name,email,password,role)
        VALUES(%s,%s,%s,%s)
        """,
        (
            name,
            email,
            hashed.decode(), # hashed_password,
            role
        )
    )

    db.commit()

    # Add Notification
    add_notification( email,
        "Welcome to SPARC! Your " + role + " account has been created successfully."
    )

    # Add Activity
    add_activity( email, "Registered as " + role)
    
    cursor.close()
    db.close()

    return jsonify({
        "message":"Registration Successful"
    })


# Login API
@app.route('/login', methods=['POST'])
def login():
    db = get_db()
    cursor = db.cursor()

    data = request.json

    email = data["email"]
    password = data["password"]
    role = data["role"]

    cursor.execute(
        """
        SELECT id,name,email,password,role,status,join_date,dark_mode
        FROM users
        WHERE email=%s AND role=%s
        """,
        (email, role)
    )

    user = cursor.fetchone()

    if not user:
        return jsonify({
            "message":"User Not Found"
        }),401

    if not bcrypt.checkpw(
        password.encode(),
        user[3].encode()
    ):
        return jsonify({
            "message":"Wrong Password"
        }),401


    cursor.execute("""
        SELECT id FROM activity
        WHERE email=%s
        AND description='Logged in'
        LIMIT 1
    """,(email,))

    exists = cursor.fetchone()

    if not exists:
        add_activity( email,"Logged in" )

    cursor.close()
    db.close()

    return jsonify({
        "id":user[0],
        "name":user[1],
        "email":user[2],
        "role":user[4],
        "status":user[5],
        "join_date":str(user[6]),
        "darkMode":bool(user[7]),

        "token":"loggedin",
        "message":"Login Successful"
    })


# Profile API
@app.route('/profile/<email>', methods=['GET'])
def profile(email):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            name, email, role, status, join_date, dark_mode
        FROM users
        WHERE email=%s
    """,(email,))

    user = cursor.fetchone()

    if not user:
        return jsonify({
            "message":"User Not Found"
        }),404

    cursor.close()
    db.close()

    return jsonify({
        "name":user[0],
        "email":user[1],
        "role":user[2],
        "status":user[3],
        "join_date":str(user[4]),
        "dark_mode":bool(user[5])
    })


# Edit Profile API
@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    db = get_db()
    cursor = db.cursor()

    data = request.json

    old_email = data["old_email"]
    name = data["name"]
    email = data["email"]

    cursor.execute("""
        UPDATE users
        SET 
            name=%s,
            email=%s
        WHERE email=%s
    """,
    (
        name,
        email,
        old_email
    ))

    db.commit()

    add_notification( email, "Profile updated successfully.")

    add_activity( email, "Updated profile information.")

    cursor.close()
    db.close()

    return jsonify({
        "message":"Profile Updated Successfully"
    })


# -----------------------------
# CHANGE PASSWORD
@app.route("/change-password", methods=["POST"])
def change_password():
    db = get_db()
    cursor = db.cursor()

    data = request.json

    email = data["email"]
    old_password = data["oldPassword"]
    new_password = data["newPassword"]

    cursor.execute("""
        SELECT password
        FROM users
        WHERE email=%s
    """,
    (email,))

    user = cursor.fetchone()

    if not user:
        return jsonify({
            "message":"User Not Found"
        }),404

    if not bcrypt.checkpw(
        old_password.encode(),
        user[0].encode()
    ):

        return jsonify({
            "message":"Old Password Incorrect"
        }),401

    hashed = bcrypt.hashpw(
        new_password.encode(),
        bcrypt.gensalt()
    ).decode()

    cursor.execute("""
        UPDATE users
        SET password=%s
        WHERE email=%s
    """,
    (
        hashed,
        email
    ))

    db.commit()

    add_notification( email, "Password changed successfully.")

    add_activity( email, "Changed account password.")

    cursor.close()
    db.close()

    return jsonify({
        "message":"Password Updated Successfully"
    })


# -----------------------------
# DARK MODE
@app.route("/toggle-darkmode", methods=["POST"])
def toggle_darkmode():
    db = get_db()
    cursor = db.cursor()

    data = request.json

    email = data["email"]

    cursor.execute("""
        SELECT dark_mode
        FROM users
        WHERE email=%s
    """,
    (email,))

    result = cursor.fetchone()

    if not result:

        return jsonify({
            "message":"User Not Found"
        }),404

    current = bool(result[0])

    new_value = not current

    cursor.execute("""
        UPDATE users
        SET dark_mode=%s
        WHERE email=%s
    """,
    (
        new_value,
        email
    ))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        "message":"Dark Mode Updated",
        "darkMode":new_value
    })
    

# Food Donation API
@app.route('/add_donation', methods=['POST'])
def add_donation():
    db = get_db()
    cursor = db.cursor()

    data = request.json

    donor_email = data["email"]
    food_type = data['food_type']
    quantity = data['quantity']
    expiry_time = data['expiry_time']
    location = data['location']

    sql = """
    INSERT INTO food_donations
    (donor_email, food_type, quantity, expiry_time, location)
    VALUES (%s,%s,%s,%s,%s)
    """

    values = (
        donor_email,
        food_type,
        quantity,
        expiry_time,
        location
    )

    cursor.execute(sql, values)

    db.commit()

    add_notification( donor_email, "Food donation submitted successfully.")
    add_activity( donor_email, "Donated " + str(quantity) + " " + food_type)

    cursor.close()
    db.close()

    return jsonify({
        "message":"Food Donation Submitted Successfully"
    })


# Get Donations
@app.route('/get_donations', methods=['GET'])
def get_donations():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    SELECT *
    FROM food_donations
    ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    donations = []

    for row in rows:
        donations.append({
            "id":row[0],
            "food_type":row[1],
            "quantity":row[2],
            "expiry_time":str(row[3]),
            "location":row[4],
            "status":row[5]
        })

    cursor.close()
    db.close()

    return jsonify(donations)


# Benificiary Registration
@app.route('/register_beneficiary', methods=['POST'])
def register_beneficiary():
    db = get_db()
    cursor = db.cursor()

    data = request.json
    registered_by = data["email"]
    name = data['name']
    phone = data['phone']
    location = data['location']
    support = data['support']

    sql = """
    INSERT INTO beneficiaries
    (
      registered_by,
      full_name,
      phone,
      location,
      support_type
    )
    VALUES(%s,%s,%s,%s,%s)
    """

    values = (
      registered_by,
      name,
      phone,
      location,
      support
    )

    cursor.execute(sql,values)

    db.commit()

    add_notification( registered_by, "Beneficiary registered successfully.")

    add_activity( registered_by, "Registered beneficiary " + name)

    cursor.close()
    db.close()

    return jsonify({
      "message":"Beneficiary Registered Successfully"
    })
    

# Apply Job
@app.route('/apply_job', methods=['POST'])
def apply_job():
    db = get_db()
    cursor = db.cursor()

    data = request.json
    applicant_email = data["email"]

    job_id = data['job_id']
    name = data['name']
    phone = data['phone']
    skills = data['skills']

    sql = """
    INSERT INTO job_applications
    (
        applicant_email,
        job_id,
        applicant_name,
        applicant_phone,
        applicant_skills
    )
    VALUES (%s,%s,%s,%s,%s)
    """

    values = (
        applicant_email,
        job_id,
        name,
        phone,
        skills
    )

    cursor.execute(sql, values)

    db.commit()

    add_notification( applicant_email, "Job application submitted successfully.")

    add_activity( applicant_email, "Applied for Job ID " + str(job_id))

    cursor.close()
    db.close()

    return jsonify({
        "message":"Application Submitted Successfully"
    })


# Get Applicaions
@app.route('/get_applications' , methods=["GET"])
def get_applications():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            id,
            job_id,
            applicant_name,
            applicant_phone,
            applicant_skills,
            status
        FROM job_applications
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    applications = []

    for row in rows:

        applications.append({

            "id":row[0],
            "job_id":row[1],
            "name":row[2],
            "phone":row[3],
            "skills":row[4],
            "status":row[5]
        })

    cursor.close()
    db.close()

    return jsonify(applications) 


# Roles
@app.route('/api/dashboard/<role>/<email>', methods=['GET'])
def dashboard(role, email):
    db = get_db()
    cursor = db.cursor()

    """elif role == "NGO":
        cursor.execute("SELECT COUNT(*) FROM beneficiaries")
        beneficiaries = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM food_donations")
        donations = cursor.fetchone()[0]

        return jsonify({
            "beneficiaries": beneficiaries,
            "donations": donations
    })"""


    if role == "NGO":
        # Beneficiaries Registered
        cursor.execute("""
            SELECT COUNT(*)
            FROM beneficiaries
            WHERE registered_by=%s
        """,(email,))

        beneficiaries = cursor.fetchone()[0]

        # Food Donations
        cursor.execute("""
            SELECT COUNT(*)
            FROM food_donations
        """)

        donations = cursor.fetchone()[0]

        # Volunteers
        cursor.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE role='Volunteer'
        """)

        volunteers = cursor.fetchone()[0]

        # Notification Count
        cursor.execute("""
            SELECT COUNT(*)
            FROM notifications
            WHERE email=%s
            AND is_read=FALSE
        """,(email,))

        notifications = cursor.fetchone()[0]

        # Today's Activity
        cursor.execute("""
            SELECT COUNT(*)
            FROM activity
            WHERE email=%s
            AND DATE(created_at)=CURDATE()
        """,(email,))

        today_activity = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM beneficiaries
            WHERE status='Pending'
        """)

        pending_beneficiaries = cursor.fetchone()[0]

        return jsonify({
            "beneficiaries": beneficiaries,
            "pending_beneficiaries": pending_beneficiaries,
            "donations": donations,
            "volunteers": volunteers,
            "notifications": notifications,
            "today_activity": today_activity
        })


        '''elif role == "Donor":
        cursor.execute("SELECT COUNT(*) FROM food_donations")
        donations = cursor.fetchone()[0]

        cursor.execute("""
            SELECT SUM(CAST(quantity AS UNSIGNED))
            FROM food_donations
        """)
        total_food = cursor.fetchone()[0] or 0

        return jsonify({
            "donations": donations,
            "food_quantity": total_food
        })'''

    elif role == "Donor":
        # Total Donations
        cursor.execute("""
            SELECT COUNT(*)
            FROM food_donations
            WHERE donor_email=%s
        """,(email,))

        donations = cursor.fetchone()[0]

        # Total Food Quantity
        cursor.execute("""
            SELECT
            SUM(CAST(quantity AS UNSIGNED))
            FROM food_donations
            WHERE donor_email=%s
        """,(email,))

        total_food = cursor.fetchone()[0] or 0

        # Pending Donations
        cursor.execute("""
            SELECT COUNT(*)
            FROM food_donations
            WHERE donor_email=%s
            AND status='Pending'
        """,(email,))

        pending = cursor.fetchone()[0]

        # Completed Donations
        cursor.execute("""
            SELECT COUNT(*)
            FROM food_donations
            WHERE donor_email=%s
            AND status='Completed'
        """,(email,))

        completed = cursor.fetchone()[0]

        # Notification Count
        cursor.execute("""
            SELECT COUNT(*)
            FROM notifications
            WHERE email=%s
            AND is_read=FALSE
        """,(email,))

        notifications = cursor.fetchone()[0]

        # Today's Activity
        cursor.execute("""
            SELECT COUNT(*)
            FROM activity
            WHERE email=%s
            AND DATE(created_at)=CURDATE()
        """,(email,))

        today_activity = cursor.fetchone()[0]


        return jsonify({
            "donations": donations,
            "food_quantity": total_food,
            "pending": pending,
            "completed": completed,
            "notifications": notifications,
            "today_activity": today_activity
        })


        '''elif role == "Employer":
        cursor.execute("SELECT COUNT(*) FROM jobs")
        jobs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM job_applications")
        applications = cursor.fetchone()[0]

        return jsonify({
            "jobs": jobs,
            "applications": applications
        })'''


    elif role == "Employer":
        # Jobs Posted
        cursor.execute("""
            SELECT COUNT(*)
            FROM jobs
            WHERE posted_by=%s
        """,(email,))

        jobs = cursor.fetchone()[0]

        # Applications Received
        cursor.execute("""
            SELECT COUNT(*)
            FROM job_applications
            WHERE job_id IN (
                SELECT id
                FROM jobs
                WHERE posted_by=%s
            )
        """,(email,))

        applications = cursor.fetchone()[0]

        # Open Jobs
        cursor.execute("""
            SELECT COUNT(*)
            FROM jobs
            WHERE posted_by=%s
            AND status='Open'
        """,(email,))

        open_jobs = cursor.fetchone()[0]

        # Notification Count
        cursor.execute("""
            SELECT COUNT(*)
            FROM notifications
            WHERE email=%s
            AND is_read=FALSE
        """,(email,))

        notifications = cursor.fetchone()[0]

        # Today's Activity
        cursor.execute("""
            SELECT COUNT(*)
            FROM activity
            WHERE email=%s
            AND DATE(created_at)=CURDATE()
        """,(email,))

        today_activity = cursor.fetchone()[0]

        return jsonify({
            "jobs": jobs,
            "applications": applications,
            "open_jobs": open_jobs,
            "notifications": notifications,
            "today_activity": today_activity
        })

    
    elif role == "Volunteer":
        # Pending Beneficiaries
        cursor.execute("""
            SELECT COUNT(*)
            FROM beneficiaries
            WHERE registered_by=%s
            AND status='Pending'
        """,(email,))

        pending_beneficiaries = cursor.fetchone()[0]

        # Total Registered Beneficiaries
        cursor.execute("""
            SELECT COUNT(*)
            FROM beneficiaries
            WHERE registered_by=%s
        """,(email,))

        beneficiaries = cursor.fetchone()[0]

        # Job Applications
        cursor.execute("""
            SELECT COUNT(*)
            FROM job_applications
            WHERE applicant_email=%s
        """,(email,))

        applications = cursor.fetchone()[0]

        # Notification Count
        cursor.execute("""
            SELECT COUNT(*)
            FROM notifications
            WHERE email=%s
            AND is_read=FALSE
        """,(email,))

        notifications = cursor.fetchone()[0]

        # Today's Activity
        cursor.execute("""
            SELECT COUNT(*)
            FROM activity
            WHERE email=%s
            AND DATE(created_at)=CURDATE()
        """,(email,))

        today_activity = cursor.fetchone()[0]

        return jsonify({
            "pending_beneficiaries": pending_beneficiaries,
            "beneficiaries": beneficiaries,
            "applications": applications,
            "notifications": notifications,
            "today_activity": today_activity
        })


    elif role == "Admin":
        # Total Users
        print("Step 1")
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        print("Step 2")
        cursor.execute("SELECT COUNT(*) FROM beneficiaries")
        beneficiaries = cursor.fetchone()[0]
        print("Step 3")
        cursor.execute("SELECT COUNT(*) FROM food_donations")
        donations = cursor.fetchone()[0]
        print("Step 4")
        cursor.execute("SELECT COUNT(*) FROM jobs")
        jobs = cursor.fetchone()[0]
        print("Step 5")
        cursor.execute("SELECT COUNT(*) FROM job_applications")
        applications = cursor.fetchone()[0]

        # Notification Count
        cursor.execute("""
            SELECT COUNT(*)
            FROM notifications
            WHERE email=%s
            AND is_read=FALSE
        """,(email,))

        notifications = cursor.fetchone()[0]

        # Today's Activity
        cursor.execute("""
            SELECT COUNT(*)
            FROM activity
            WHERE email=%s
            AND DATE(created_at)=CURDATE()
        """,(email,))

        today_activity = cursor.fetchone()[0]

        return jsonify({
            "users": users,
            "beneficiaries": beneficiaries,
            "donations": donations,
            "jobs": jobs,
            "applications": applications,
            "notifications": notifications,
            "today_activity": today_activity
        })

    cursor.close()
    db.close()

    return jsonify({
        "message":"Role not found"
    }),404


# Dashboard Chart API
@app.route('/dashboard_chart/<role>/<email>', methods=['GET'])
def dashboard_chart(role, email):

    db = get_db()
    cursor = db.cursor()

    if role == "Donor":

        cursor.execute("""
            SELECT COUNT(*)
            FROM food_donations
            WHERE donor_email=%s
            AND status='Pending'
        """,(email,))

        pending = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM food_donations
            WHERE donor_email=%s
            AND status='Completed'
        """,(email,))

        completed = cursor.fetchone()[0]

        cursor.execute("""
            SELECT
            SUM(CAST(quantity AS UNSIGNED))
            FROM food_donations
            WHERE donor_email=%s
        """,(email,))

        quantity = cursor.fetchone()[0] or 0

        return jsonify({

            "labels":[
                "Pending",
                "Completed",
                "Food Qty"
            ],

            "values":[
                pending,
                completed,
                quantity
            ]

        })


    elif role == "Volunteer":

        cursor.execute("""
            SELECT COUNT(*)
            FROM beneficiaries
            WHERE registered_by=%s
            AND status='Pending'
        """,(email,))

        pending = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM beneficiaries
            WHERE registered_by=%s
            AND status='Completed'
        """,(email,))

        completed = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM job_applications
            WHERE applicant_email=%s
        """,(email,))

        applications = cursor.fetchone()[0]

        return jsonify({

            "labels":[
                "Pending",
                "Completed",
                "Applications"
            ],

            "values":[
                pending,
                completed,
                applications
            ]

        })


    elif role == "NGO":

        cursor.execute("""
            SELECT COUNT(*)
            FROM beneficiaries
            WHERE registered_by=%s
        """,(email,))

        beneficiaries = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM food_donations
        """)

        donations = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE role='Volunteer'
        """)

        volunteers = cursor.fetchone()[0]

        return jsonify({

            "labels":[
                "Beneficiaries",
                "Donations",
                "Volunteers"
            ],

            "values":[
                beneficiaries,
                donations,
                volunteers
            ]

        })


    elif role == "Employer":

        cursor.execute("""
            SELECT COUNT(*)
            FROM jobs
            WHERE posted_by=%s
            AND status='Open'
        """,(email,))

        open_jobs = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM jobs
            WHERE posted_by=%s
            AND status='Closed'
        """,(email,))

        closed_jobs = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM job_applications
            WHERE job_id IN(
                SELECT id
                FROM jobs
                WHERE posted_by=%s
            )
        """,(email,))

        applications = cursor.fetchone()[0]

        return jsonify({

            "labels":[
                "Open",
                "Closed",
                "Applications"
            ],

            "values":[
                open_jobs,
                closed_jobs,
                applications
            ]

        })


    elif role == "Admin":

        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM food_donations")
        donations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM beneficiaries")
        beneficiaries = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs")
        jobs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM job_applications")
        applications = cursor.fetchone()[0]

        return jsonify({

            "labels":[
                "Users",
                "Donations",
                "Beneficiaries",
                "Jobs",
                "Applications"
            ],

            "values":[
                users,
                donations,
                beneficiaries,
                jobs,
                applications
            ]

        })

    cursor.close()
    db.close()

    return jsonify({
        "labels":[],
        "values":[]
    })


# Notifications API
@app.route('/get_notifications/<email>' , methods=["GET"])
def get_notifications(email):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT title,
        created_at
        FROM notifications
        WHERE email=%s
        ORDER BY created_at DESC
        LIMIT 20
    """,
    (email,))

    rows = cursor.fetchall()
    notifications = []

    for row in rows:
        notifications.append({
            "title": row[0],
            "time":row[1].strftime("%Y-%m-%dT%H:%M:%S")
        })

    cursor.close()
    db.close()

    return jsonify(notifications)



# Activity API
@app.route('/get_activity/<email>', methods=["GET"])
def get_activity(email):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT description,
        created_at
        FROM activity
        WHERE email=%s
        ORDER BY created_at DESC
        LIMIT 20
    """,
    (email,))

    rows = cursor.fetchall()

    activity = []

    for row in rows:
        activity.append({
            "description": row[0],
            "time":row[1].strftime("%Y-%m-%dT%H:%M:%S")
        })

    cursor.close()
    db.close()

    return jsonify(activity)


@app.route("/api/admin/user-counts", methods=["GET"])
def admin_user_counts():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT role, COUNT(*) AS total
        FROM users
        GROUP BY role
    """)

    rows = cursor.fetchall()

    counts = {
        "Volunteer": 0,
        "NGO": 0,
        "Donor": 0,
        "Employer": 0
    }

    for row in rows:
        counts[row["role"]] = row["total"]

    cursor.close()
    db.close()

    return jsonify(counts)


@app.route("/api/admin/users/<role>", methods=["GET"])
def admin_get_users(role):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            role,
            status,
            join_date
        FROM users
        WHERE role=%s
        ORDER BY join_date DESC
    """, (role,))

    users = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(users)


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id=%s",
        (user_id,)
    )

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "message": "User deleted successfully"
    })


@app.route("/api/admin/users", methods=["GET"])
def get_all_users():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            role,
            status,
            join_date
        FROM users
        ORDER BY role,name
    """)

    users = cursor.fetchall()
    cursor.close()
    db.close()

    return jsonify(users)


# -----------------------------
# HOME
@app.route("/")
def home():
    return jsonify({
        "message": "SPARC Flask Backend Running Successfully"
    })

# -----------------------------
# START SERVER
if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        port=int(os.getenv("PORT", 5001))
    )