from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import bcrypt
import os
import random
import requests
import cloudinary
from cloudinary.utils import api_sign_request

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


from dotenv import load_dotenv
load_dotenv()

# CLOUDINARY CONFIGURATION
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# EMAIL CONFIGURATION (BREVO)
SECRET_KEY = os.getenv("SECRET_KEY")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

print("MAIL_DEFAULT_SENDER =", MAIL_DEFAULT_SENDER)

import string
from datetime import datetime, timedelta


# ==========================================
# CLOUDINARY SIGNED UPLOAD
@app.route('/api/cloudinary/sign', methods=['POST'])
def cloudinary_sign():
    timestamp = request.json.get("timestamp")

    if not timestamp:
        return jsonify({
            "success": False,
            "message": "Timestamp is required."
        }), 400

    params_to_sign = {
        "folder": "sparc/donation_proofs",
        "source": "uw",
        "timestamp": timestamp,
        "upload_preset": "sparc_donation_proof"
    }

    signature = api_sign_request(
        params_to_sign,
        CLOUDINARY_API_SECRET
    )

    return jsonify({
        "success": True,
        "signature": signature,
        "timestamp": timestamp,
        "api_key": CLOUDINARY_API_KEY,
        "cloud_name": CLOUDINARY_CLOUD_NAME,
        "upload_preset": "sparc_donation_proof"
    })


# Store OTP with expiry
otp_storage = {}

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


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
    cursor.close()
    db.close()


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
    cursor.close()
    db.close()


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
        WHERE email=%s 
        AND role=%s
        AND status='Active'
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
            "message":"Incorrect password. Please try again."
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


# ==========================================
# AVAILABLE FOOD DONATIONS
@app.route('/get_available_donations', methods=['GET'])
def get_available_donations():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            food_type,
            quantity,
            expiry_time,
            location,
            status,
            created_at,
            donor_email
        FROM food_donations
        WHERE status='Pending'
        AND volunteer_email IS NULL
        ORDER BY id DESC
    """)

    donations = cursor.fetchall()

    cursor.close()
    db.close()

    for donation in donations:
        if donation["expiry_time"]:
            donation["expiry_time"] = donation["expiry_time"].strftime(
                "%Y-%m-%dT%H:%M:%S"
            )

        if donation["created_at"]:
            donation["created_at"] = donation["created_at"].strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
    return jsonify(donations)


# ==========================================
# VOLUNTEER'S ASSIGNED DONATIONS
@app.route('/get_my_donations/<email>', methods=['GET'])
def get_my_donations(email):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            food_type,
            quantity,
            expiry_time,
            location,
            status,
            created_at,
            donor_email,
            volunteer_email,
            assigned_at,
            picked_up_at,
            out_for_delivery_at,
            beneficiary_id,
            completed_at,
            proof_photo,
            completion_notes
        FROM food_donations
        WHERE volunteer_email=%s
        ORDER BY id DESC
    """, (email,))

    donations = cursor.fetchall()

    cursor.close()
    db.close()

    for donation in donations:
        for field in [
            "expiry_time",
            "created_at",
            "assigned_at",
            "picked_up_at",
            "out_for_delivery_at",
            "completed_at"
        ]:

            if donation[field]:
                donation[field] = donation[field].strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
    return jsonify(donations)


# ==========================================
# TAKE DONATION RESPONSIBILITY
@app.route('/take_donation/<int:donation_id>', methods=['POST'])
def take_donation(donation_id):
    data = request.json

    volunteer_email = data.get("email")

    if not volunteer_email:
        return jsonify({
            "success": False,
            "message": "Volunteer email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get volunteer details
    cursor.execute("""
        SELECT name, role, status
        FROM users
        WHERE email=%s
    """, (volunteer_email,))

    volunteer = cursor.fetchone()

    if not volunteer:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Volunteer account not found."
        }), 404

    if volunteer["role"] != "Volunteer":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only volunteers can take donation responsibility."
        }), 403

    if volunteer["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Your account is not active."
        }), 403

    # IMPORTANT:
    # Only one volunteer can successfully claim the donation.
    cursor.execute("""
        UPDATE food_donations
        SET
            volunteer_email=%s,
            status='Assigned',
            assigned_at=NOW()
        WHERE id=%s
        AND status='Pending'
        AND volunteer_email IS NULL
    """, (
        volunteer_email,
        donation_id
    ))

    # rowcount tells us whether the UPDATE actually happened
    if cursor.rowcount == 0:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Sorry, this donation has already been taken by another volunteer."
        }), 409

    # Get admin accounts
    cursor.execute("""
        SELECT email
        FROM users
        WHERE role='Admin'
        AND status='Active'
    """)

    admins = cursor.fetchall()

    cursor.close()
    db.close()

    # Notify every active Admin
    for admin in admins:
        add_notification(
            admin["email"],
            "Volunteer " + volunteer["name"] +
            " has taken responsibility for Donation #" +
            str(donation_id) + "."
        )

    # Add volunteer activity
    add_activity(
        volunteer_email,
        "Took responsibility for Donation #" +
        str(donation_id)
    )
    return jsonify({
        "success": True,
        "message": "Donation responsibility taken successfully."
    })


# ==========================================
# PICK UP DONATION
@app.route('/pick_donation/<int:donation_id>', methods=['POST'])
def pick_donation(donation_id):
    data = request.json

    volunteer_email = data.get("email")

    if not volunteer_email:
        return jsonify({
            "success": False,
            "message": "Volunteer email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Make sure this donation belongs to this volunteer
    cursor.execute("""
        SELECT
            id,
            volunteer_email,
            status
        FROM food_donations
        WHERE id=%s
    """, (donation_id,))

    donation = cursor.fetchone()

    if not donation:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Donation not found."
        }), 404

    if donation["volunteer_email"] != volunteer_email:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not responsible for this donation."
        }), 403

    if donation["status"] != "Assigned":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This donation cannot be marked as picked up."
        }), 400

    cursor.execute("""
        UPDATE food_donations
        SET
            status='Picked Up',
            picked_up_at=NOW()
        WHERE id=%s
        AND volunteer_email=%s
        AND status='Assigned'
    """, (
        donation_id,
        volunteer_email
    ))

    cursor.close()
    db.close()

    # Admin notification
    db2 = get_db()
    cursor2 = db2.cursor(dictionary=True)

    cursor2.execute("""
        SELECT email
        FROM users
        WHERE role='Admin'
        AND status='Active'
    """)

    admins = cursor2.fetchall()

    cursor2.close()
    db2.close()

    for admin in admins:
        add_notification(
            admin["email"],
            "Donation #" + str(donation_id) +
            " has been picked up by Volunteer " +
            volunteer_email + "."
        )

    add_activity(
        volunteer_email,
        "Picked up Donation #" + str(donation_id)
    )

    return jsonify({
        "success": True,
        "message": "Donation marked as picked up."
    })


# ==========================================
# START DELIVERY
@app.route('/start_delivery/<int:donation_id>', methods=['POST'])
def start_delivery(donation_id):
    data = request.json

    volunteer_email = data.get("email")

    if not volunteer_email:
        return jsonify({
            "success": False,
            "message": "Volunteer email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            volunteer_email,
            status
        FROM food_donations
        WHERE id=%s
    """, (donation_id,))

    donation = cursor.fetchone()

    if not donation:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Donation not found."
        }), 404

    if donation["volunteer_email"] != volunteer_email:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not responsible for this donation."
        }), 403

    if donation["status"] != "Picked Up":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Donation must be picked up before starting delivery."
        }), 400

    cursor.execute("""
        UPDATE food_donations
        SET
            status='Out for Delivery',
            out_for_delivery_at=NOW()
        WHERE id=%s
        AND volunteer_email=%s
        AND status='Picked Up'
    """, (
        donation_id,
        volunteer_email
    ))
    cursor.close()
    db.close()

    # Notify Admin
    db2 = get_db()
    cursor2 = db2.cursor(dictionary=True)

    cursor2.execute("""
        SELECT email
        FROM users
        WHERE role='Admin'
        AND status='Active'
    """)

    admins = cursor2.fetchall()

    cursor2.close()
    db2.close()

    for admin in admins:
        add_notification(
            admin["email"],
            "Donation #" + str(donation_id) +
            " is now out for delivery."
        )

    add_activity(
        volunteer_email,
        "Started delivery for Donation #" +
        str(donation_id)
    )

    return jsonify({
        "success": True,
        "message": "Donation is now out for delivery."
    })


# ==========================================
# GET AVAILABLE BENEFICIARIES
@app.route('/get_beneficiaries', methods=['GET'])
def get_beneficiaries():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            full_name,
            phone,
            location,
            support_type,
            status
        FROM beneficiaries
        WHERE status='Pending'
        ORDER BY id DESC
    """)

    beneficiaries = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(beneficiaries)



# ==========================================
# COMPLETE FOOD DONATION
# ==========================================

@app.route('/complete_donation/<int:donation_id>', methods=['POST'])
def complete_donation(donation_id):

    data = request.json

    volunteer_email = data.get("email")
    beneficiary_id = data.get("beneficiary_id")
    completion_notes = data.get("completion_notes", "")
    proof_photo = data.get("proof_photo")

    if not proof_photo:
        return jsonify({
            "success": False,
            "message": "Donation proof photo is required."
        }), 400

    if not volunteer_email:
        return jsonify({
            "success": False,
            "message": "Volunteer email is required."
        }), 400

    if not beneficiary_id:
        return jsonify({
            "success": False,
            "message": "Please select a beneficiary."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # ------------------------------------------
    # 1. Check donation
    # ------------------------------------------
    cursor.execute("""
        SELECT
            id,
            food_type,
            quantity,
            donor_email,
            volunteer_email,
            status
        FROM food_donations
        WHERE id=%s
    """, (donation_id,))

    donation = cursor.fetchone()

    if not donation:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Donation not found."
        }), 404

    # ------------------------------------------
    # 2. Check assigned volunteer
    # ------------------------------------------
    if donation["volunteer_email"] != volunteer_email:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not responsible for this donation."
        }), 403

    # ------------------------------------------
    # 3. Check current status
    # ------------------------------------------
    if donation["status"] != "Out for Delivery":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message":
                "Donation must be out for delivery before it can be completed."
        }), 400

    # ------------------------------------------
    # 4. Check beneficiary
    # ------------------------------------------
    cursor.execute("""
        SELECT
            id,
            full_name,
            phone,
            location,
            support_type,
            status
        FROM beneficiaries
        WHERE id=%s
    """, (beneficiary_id,))

    beneficiary = cursor.fetchone()

    if not beneficiary:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Beneficiary not found."
        }), 404

    # ------------------------------------------
    # 5. Complete donation
    # ------------------------------------------
    cursor.execute("""
        UPDATE food_donations
        SET
            status='Completed',
            beneficiary_id=%s,
            completed_at=NOW(),
            proof_photo=%s,
            completion_notes=%s
        WHERE id=%s
        AND volunteer_email=%s
        AND status='Out for Delivery'
    """, (
        beneficiary_id,
        proof_photo,
        completion_notes,
        donation_id,
        volunteer_email
    ))

    if cursor.rowcount == 0:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message":
                "Donation could not be completed. Please try again."
        }), 409

    # ------------------------------------------
    # 6. Get volunteer name
    # ------------------------------------------
    cursor.execute("""
        SELECT name
        FROM users
        WHERE email=%s
    """, (volunteer_email,))

    volunteer = cursor.fetchone()

    volunteer_name = (
        volunteer["name"]
        if volunteer
        else volunteer_email
    )

    # ------------------------------------------
    # 7. Get active Admins
    # ------------------------------------------
    cursor.execute("""
        SELECT email
        FROM users
        WHERE role='Admin'
        AND status='Active'
    """)

    admins = cursor.fetchall()

    # ------------------------------------------
    # 8. Get donor email
    # ------------------------------------------
    donor_email = donation["donor_email"]

    cursor.close()
    db.close()

    # ------------------------------------------
    # 9. Notify Admin
    # ------------------------------------------
    for admin in admins:
        add_notification(
            admin["email"],
            "Donation #" +
            str(donation_id) +
            " was successfully delivered by Volunteer " +
            volunteer_name +
            " to " +
            beneficiary["full_name"] +
            "."
        )

    # ------------------------------------------
    # 10. Notify Donor
    # ------------------------------------------
    if donor_email:
        add_notification(
            donor_email,
            "Your food donation #" +
            str(donation_id) +
            " was successfully delivered to " +
            beneficiary["full_name"] +
            ". Thank you for supporting the community!"
        )

    # ------------------------------------------
    # 11. Volunteer activity
    # ------------------------------------------
    add_activity(
        volunteer_email,
        "Successfully delivered Donation #" +
        str(donation_id) +
        " to " +
        beneficiary["full_name"]
    )


    return jsonify({
        "success": True,
        "message": "Donation completed successfully."
    })


# ==========================================
# ADMIN - GET ALL FOOD DONATIONS
@app.route('/api/admin/donations', methods=['GET'])
def admin_get_donations():

    admin_email = request.args.get("email")

    if not admin_email:
        return jsonify({
            "success": False,
            "message": "Admin email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Verify that the requesting account is an active Admin
    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (admin_email,))

    admin = cursor.fetchone()

    if not admin:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404

    if admin["role"] != "Admin":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    if admin["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin account is not active."
        }), 403

    cursor.execute("""
        SELECT
            fd.id,
            fd.food_type,
            fd.quantity,
            fd.expiry_time,
            fd.location,
            fd.status,
            fd.created_at,
            fd.donor_email,

            fd.volunteer_email,
            fd.assigned_at,
            fd.picked_up_at,
            fd.out_for_delivery_at,

            fd.beneficiary_id,
            fd.completed_at,
            fd.proof_photo,
            fd.completion_notes,

            u.name AS volunteer_name,

            b.full_name AS beneficiary_name,
            b.phone AS beneficiary_phone,
            b.location AS beneficiary_location

        FROM food_donations fd

        LEFT JOIN users u
            ON fd.volunteer_email = u.email

        LEFT JOIN beneficiaries b
            ON fd.beneficiary_id = b.id

        ORDER BY fd.id DESC
    """)

    donations = cursor.fetchall()

    for donation in donations:
        for field in [
            "expiry_time",
            "created_at",
            "assigned_at",
            "picked_up_at",
            "out_for_delivery_at",
            "completed_at"
        ]:

            if donation[field]:

                donation[field] = (
                    donation[field]
                    .strftime("%Y-%m-%dT%H:%M:%S")
                )
    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "donations": donations
    })


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


@app.route("/api/admin/users/<int:user_id>", methods=["PUT"])
def toggle_user_status(user_id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT status
        FROM users
        WHERE id=%s
    """,(user_id,))

    result = cursor.fetchone()

    if not result:
        return jsonify({
            "success":False,
            "message":"User not found"
        }),404

    current_status=result[0]

    new_status="Inactive" if current_status=="Active" else "Active"

    cursor.execute("""
        UPDATE users
        SET status=%s
        WHERE id=%s
    """,(new_status,user_id))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        "success":True,
        "status":new_status,
        "message":"User status updated successfully."
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


@app.route("/forgot_password", methods=["POST"])
def forgot_password():

    data = request.json
    email = data.get("email")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email=%s",
        (email,)
    )

    user = cursor.fetchone()

    if not user:
        return jsonify({
            "success": False,
            "message": "Email not registered"
        }),404

    otp = generate_otp()

    otp_storage[email] = {
        "otp": otp,
        "expires": datetime.now() + timedelta(minutes=10)
    }


    html_body = f"""
    <html>
    <body style="font-family:Arial,sans-serif;">
        <h2>SPARC Password Reset</h2>

        <p>Hello <b>{user['name']}</b>,</p>

        <p>Your OTP is:</p>

        <h1 style="color:#0f7a2f;">{otp}</h1>

        <p>This OTP is valid for <b>10 minutes</b>.</p>

        <p>If you didn't request this password reset, please ignore this email.</p>

        <br>

        <p>Regards,<br><b>SPARC Team</b></p>
    </body>
    </html>
    """

    try:
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }

        payload = {
            "sender": {
                "email": MAIL_DEFAULT_SENDER,
                "name": "SPARC"
            },

            "to": [
                {
                    "email": email
                }
            ],

            "subject": "SPARC Password Reset OTP",

            "htmlContent": html_body
        }

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        print("EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        import traceback

        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }),500

    add_notification(
        email,
        "Password reset OTP sent to your email."
    )

    add_activity(
        email,
        "Requested password reset OTP"
    )

    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "message": "OTP sent successfully"
    })


@app.route("/verify_otp", methods=["POST"])
def verify_otp():

    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    if email not in otp_storage:
        return jsonify({
            "success": False,
            "message": "OTP not found"
        }),400

    saved = otp_storage[email]

    if datetime.now() > saved["expires"]:
        del otp_storage[email]
        return jsonify({
            "success": False,
            "message": "OTP expired"
        }),400

    if otp != saved["otp"]:
        return jsonify({
            "success": False,
            "message": "Invalid OTP"
        }),400

    otp_storage[email]["verified"] = True

    return jsonify({
        "success": True,
        "message": "OTP Verified"
    })



@app.route("/reset_password", methods=["POST"])
def reset_password():

    data = request.json

    email = data.get("email")
    password = data.get("password")

    if email not in otp_storage:
        return jsonify({
            "success": False,
            "message": "OTP verification required"
        }),400

    if not otp_storage[email].get("verified"):
        return jsonify({
            "success": False,
            "message": "Please verify your OTP first."
    }),400

    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE users SET password=%s WHERE email=%s",
        (hashed, email)
    )

    db.commit()
    cursor.close()
    db.close()

    add_notification(
        email,
        "Your password has been reset successfully."
    )

    add_activity(
        email,
        "Password reset successfully."
    )

    del otp_storage[email]

    return jsonify({
        "success": True,
        "message": "Password updated successfully"
    })



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