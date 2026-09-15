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

ADMIN_EMAIL = os.getenv(
    "ADMIN_EMAIL"
)

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
    try:
        data = request.get_json(silent=True) or {}

        timestamp = data.get("timestamp")

        if not timestamp:
            return jsonify({
                "success": False,
                "message": "Timestamp is required."
            }), 400

        # Make sure Render has the Cloudinary credentials
        if not CLOUDINARY_CLOUD_NAME:
            return jsonify({
                "success": False,
                "message": "Cloudinary cloud name is not configured."
            }), 500

        if not CLOUDINARY_API_KEY:
            return jsonify({
                "success": False,
                "message": "Cloudinary API key is not configured."
            }), 500

        if not CLOUDINARY_API_SECRET:
            return jsonify({
                "success": False,
                "message": "Cloudinary API secret is not configured."
            }), 500

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

    except Exception as error:
        print(
            "Cloudinary signature error:",
            str(error)
        )

        return jsonify({
            "success": False,
            "message": "Unable to generate Cloudinary upload signature."
        }), 500



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

    allowed_roles = ["Volunteer", "NGO", "Donor", "Employer"]

    if role not in allowed_roles:
        return jsonify({
            "success": False,
            "message": "Invalid registration role."
        }), 400

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

    # Only the designated email can use the Admin role
    if role == "Admin" and email.lower() != ADMIN_EMAIL.lower():
        return jsonify({
            "message": "This account is not authorized as Admin."
        }), 403

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

    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (
        donor_email,
    ))

    donor = cursor.fetchone()

    if not donor:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Donor account not found."
        }), 404

    if donor[0] != "Donor":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only donors can add food donations."
        }), 403

    if donor[1] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Donor account is not active."
        }), 403


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

    volunteer_email = request.args.get("email")

    if not volunteer_email:
        return jsonify({
            "success": False,
            "message": "Volunteer email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # VERIFY VOLUNTEER
    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (volunteer_email,))

    volunteer = cursor.fetchone()

    if not volunteer:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404

    if volunteer["role"] != "Volunteer":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only volunteers can view available donations."
        }), 403

    if volunteer["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Volunteer account is not active."
        }), 403

    # GET AVAILABLE DONATIONS
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
            donation["expiry_time"] = (
                donation["expiry_time"]
                .strftime("%Y-%m-%dT%H:%M:%S")
            )

        if donation["created_at"]:
            donation["created_at"] = (
                donation["created_at"]
                .strftime("%Y-%m-%dT%H:%M:%S")
            )

    return jsonify(donations)


# ==========================================
# VOLUNTEER'S ASSIGNED DONATIONS
@app.route('/get_my_donations/<email>', methods=['GET'])
def get_my_donations(email):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (email,))

    volunteer = cursor.fetchone()

    if not volunteer:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404

    if volunteer["role"] != "Volunteer":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only volunteers can view their donations."
        }), 403

    if volunteer["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Volunteer account is not active."
        }), 403

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
    email = request.args.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (
        email,
    ))

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404

    if user["role"] not in [
        "Volunteer",
        "NGO",
        "Admin"
    ]:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not authorized to view beneficiaries."
        }), 403

    if user["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Account is not active."
        }), 403

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

    return jsonify({
        "success": True,
        "beneficiaries": beneficiaries
    })



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
        AND status='Pending'
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


'''
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
'''


@app.route('/register_beneficiary', methods=['POST'])
def register_beneficiary():

    data = request.get_json(silent=True) or {}

    registered_by = data.get("email")
    name = data.get("name")
    phone = data.get("phone")
    location = data.get("location")
    support = data.get("support")

    education = data.get("education")
    skills = data.get("skills")
    experience_years = data.get("experience_years")
    availability = data.get("availability")
    preferred_work_type = data.get("preferred_work_type")

    if not registered_by:
        return jsonify({
            "success": False,
            "message": "Registering user email is required."
        }), 400

    if not name or not phone or not location:
        return jsonify({
            "success": False,
            "message": "Name, phone and location are required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------------------------
    # VERIFY REGISTERING USER
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (registered_by,))

    registering_user = cursor.fetchone()

    if not registering_user:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Registering user account not found."
        }), 404

    if registering_user["role"] not in [
        "Volunteer",
        "NGO",
        "Admin"
    ]:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only Volunteer, NGO or Admin can register beneficiaries."
        }), 403

    if registering_user["status"] != "Active":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Registering account is not active."
        }), 403

    # --------------------------------------------------------
    # INSERT BENEFICIARY
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO beneficiaries
        (
            registered_by,
            full_name,
            phone,
            location,
            support_type,

            education,
            skills,
            experience_years,
            availability,
            preferred_work_type,

            digital_access_mode
        )
        VALUES
        (
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            'ASSISTED'
        )
    """, (
        registered_by,
        name,
        phone,
        location,
        support,

        education,
        skills,
        experience_years,
        availability,
        preferred_work_type
    ))

    beneficiary_id = cursor.lastrowid

    db.commit()

    cursor.close()
    db.close()

    add_notification(
        registered_by,
        "Beneficiary " +
        name +
        " registered successfully."
    )

    add_activity(
        registered_by,
        "Registered beneficiary " +
        name
    )

    return jsonify({
        "success": True,
        "message": "Beneficiary registered successfully.",
        "beneficiary_id": beneficiary_id
    }), 201


@app.route('/create_beneficiary_account', methods=['POST'])
def create_beneficiary_account():

    data = request.get_json(silent=True) or {}

    beneficiary_id = data.get("beneficiary_id")
    email = data.get("email")
    password = data.get("password")
    requested_by = data.get("requested_by_email")

    if not beneficiary_id or not email or not password or not requested_by:
        return jsonify({
            "success": False,
            "message": "Beneficiary ID, email, password and requesting user are required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------------------------
    # VERIFY REQUESTING USER
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (requested_by,))

    requester = cursor.fetchone()

    if not requester:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Requesting user account not found."
        }), 404

    if requester["role"] not in [
        "Volunteer",
        "NGO",
        "Admin"
    ]:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only Volunteer, NGO or Admin can activate beneficiary self-access."
        }), 403

    if requester["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Requesting account is not active."
        }), 403

    # --------------------------------------------------------
    # GET BENEFICIARY
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            full_name,
            user_id,
            digital_access_mode
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

    if beneficiary["user_id"] is not None:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This beneficiary already has a SPARC account."
        }), 409

    # --------------------------------------------------------
    # CHECK EMAIL
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id
        FROM users
        WHERE email=%s
    """, (email,))

    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This email is already registered."
        }), 409

    # --------------------------------------------------------
    # CREATE ACCOUNT
    # --------------------------------------------------------

    hashed_password = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )

    cursor.execute("""
        INSERT INTO users
        (
            name,
            email,
            password,
            role,
            status
        )
        VALUES(
            %s,
            %s,
            %s,
            'Beneficiary',
            'Active'
        )
    """, (
        beneficiary["full_name"],
        email,
        hashed_password.decode()
    ))

    user_id = cursor.lastrowid

    # --------------------------------------------------------
    # LINK BENEFICIARY TO ACCOUNT
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE beneficiaries
        SET
            user_id=%s,
            digital_access_mode='SELF'
        WHERE id=%s
    """, (
        user_id,
        beneficiary_id
    ))

    db.commit()

    cursor.close()
    db.close()

    add_notification(
        email,
        "Your SPARC self-access account has been activated."
    )

    add_activity(
        requested_by,
        "Activated self-access for beneficiary " +
        beneficiary["full_name"]
    )

    return jsonify({
        "success": True,
        "message": "Beneficiary self-access activated successfully.",
        "user_id": user_id,
        "beneficiary_id": beneficiary_id
    }), 201


@app.route('/beneficiary_profile/<int:beneficiary_id>', methods=['GET'])
def beneficiary_profile(beneficiary_id):
    email = request.args.get("email")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if user["role"] == "Beneficiary":
        cursor.execute("""
            SELECT id
            FROM beneficiaries
            WHERE id=%s
            AND user_id=%s
        """, (
            beneficiary_id,
            user["id"]
        ))

        own_profile = cursor.fetchone()

        if not own_profile:
            return 403

    cursor.execute("""
        SELECT
            b.id,
            b.full_name,
            b.phone,
            b.location,
            b.support_type,
            b.status,
            b.education,
            b.skills,
            b.experience_years,
            b.availability,
            b.preferred_work_type,
            b.digital_access_mode,
            b.user_id,

            u.email AS account_email

        FROM beneficiaries b

        LEFT JOIN users u
            ON u.id = b.user_id

        WHERE b.id=%s
    """, (beneficiary_id,))

    beneficiary = cursor.fetchone()

    cursor.close()
    db.close()

    if not beneficiary:

        return jsonify({
            "success": False,
            "message": "Beneficiary not found."
        }), 404

    return jsonify({
        "success": True,
        "beneficiary": beneficiary
    })


@app.route('/my_beneficiary_profile/<email>', methods=['GET'])
def my_beneficiary_profile(email):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            b.id,
            b.full_name,
            b.phone,
            b.location,
            b.support_type,
            b.status,
            b.education,
            b.skills,
            b.experience_years,
            b.availability,
            b.preferred_work_type,
            b.digital_access_mode,
            b.user_id,

            u.email AS account_email,
            u.role AS account_role

        FROM beneficiaries b

        INNER JOIN users u
            ON u.id = b.user_id

        WHERE u.email=%s
        AND u.role='Beneficiary'
        AND u.status='Active'
    """, (email,))

    beneficiary = cursor.fetchone()

    cursor.close()
    db.close()

    if not beneficiary:

        return jsonify({
            "success": False,
            "message": "No beneficiary profile is linked to this account."
        }), 404

    return jsonify({
        "success": True,
        "beneficiary": beneficiary
    })


'''
// Apply Job
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
'''

# ============================================================
# JOB / LIVELIHOOD APIs
# ============================================================


# ------------------------------------------------------------
# GET AVAILABLE JOBS
# ------------------------------------------------------------
@app.route('/get_jobs', methods=['GET'])
def get_jobs():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            j.id,
            j.title,
            j.duration,
            j.salary,
            j.location,
            j.description,
            j.status,
            j.created_at,
            j.posted_by,

            j.livelihood_path,
            j.wage_type,
            j.wage_amount,
            j.work_date,
            j.start_time,
            j.end_time,
            j.meeting_point,

            j.work_latitude,
            j.work_longitude,
            j.meeting_latitude,
            j.meeting_longitude,

            j.payment_commitment,
            j.payment_due_date,
            j.vacancies,
            j.requirements,

            u.name AS employer_name

        FROM jobs j

        LEFT JOIN users u
            ON u.email = j.posted_by

        WHERE j.status = 'Open'

        ORDER BY j.id DESC
    """)

    jobs = cursor.fetchall()

    cursor.close()
    db.close()

    for job in jobs:

        if job["created_at"]:
            job["created_at"] = (
                job["created_at"]
                .strftime("%Y-%m-%dT%H:%M:%S")
            )

        if job["work_date"]:
            job["work_date"] = (
                job["work_date"]
                .strftime("%Y-%m-%d")
            )

        if job["payment_due_date"]:
            job["payment_due_date"] = (
                job["payment_due_date"]
                .strftime("%Y-%m-%d")
            )

        if job["start_time"]:
            job["start_time"] = str(job["start_time"])

        if job["end_time"]:
            job["end_time"] = str(job["end_time"])

    return jsonify({
        "success": True,
        "jobs": jobs
    })


# ------------------------------------------------------------
# GET SINGLE JOB
# ------------------------------------------------------------
@app.route('/get_job/<int:job_id>', methods=['GET'])
def get_job(job_id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            j.id,
            j.title,
            j.duration,
            j.salary,
            j.location,
            j.description,
            j.status,
            j.created_at,
            j.posted_by,

            j.livelihood_path,
            j.wage_type,
            j.wage_amount,
            j.work_date,
            j.start_time,
            j.end_time,
            j.meeting_point,

            j.work_latitude,
            j.work_longitude,
            j.meeting_latitude,
            j.meeting_longitude,

            j.payment_commitment,
            j.payment_due_date,
            j.vacancies,
            j.requirements,

            u.name AS employer_name

        FROM jobs j

        LEFT JOIN users u
            ON u.email = j.posted_by

        WHERE j.id=%s
    """, (job_id,))

    job = cursor.fetchone()

    cursor.close()
    db.close()

    if not job:
        return jsonify({
            "success": False,
            "message": "Job not found."
        }), 404

    if job["created_at"]:
        job["created_at"] = (
            job["created_at"]
            .strftime("%Y-%m-%dT%H:%M:%S")
        )

    if job["work_date"]:
        job["work_date"] = (
            job["work_date"]
            .strftime("%Y-%m-%d")
        )

    if job["payment_due_date"]:
        job["payment_due_date"] = (
            job["payment_due_date"]
            .strftime("%Y-%m-%d")
        )

    if job["start_time"]:
        job["start_time"] = str(job["start_time"])

    if job["end_time"]:
        job["end_time"] = str(job["end_time"])

    return jsonify({
        "success": True,
        "job": job
    })


# ------------------------------------------------------------
# EMPLOYER: POST A JOB
# ------------------------------------------------------------
@app.route('/post_job', methods=['POST'])
def post_job():

    data = request.get_json(silent=True) or {}

    employer_email = data.get("employer_email")

    if not employer_email:
        return jsonify({
            "success": False,
            "message": "Employer email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Verify employer
    cursor.execute("""
        SELECT
            email,
            name,
            role,
            status
        FROM users
        WHERE email=%s
    """, (employer_email,))

    employer = cursor.fetchone()

    if not employer:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account not found."
        }), 404

    if employer["role"] != "Employer":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only employers can post jobs."
        }), 403

    if employer["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account is not active."
        }), 403

    title = data.get("title")
    description = data.get("description")
    location = data.get("location")

    livelihood_path = data.get(
        "livelihood_path",
        "IMMEDIATE_INCOME"
    )

    wage_type = data.get(
        "wage_type",
        "DAILY"
    )

    if wage_type not in [
        "DAILY",
        "HOURLY"
    ]:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Invalid wage type."
        }), 400

    wage_amount = data.get("wage_amount")

    vacancies = data.get("vacancies", 1)

    if not title or not description or not location:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Title, description and location are required."
        }), 400

    if wage_amount is None:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Wage amount is required."
        }), 400

    if livelihood_path not in [
        "IMMEDIATE_INCOME",
        "CAREER_GROWTH"
    ]:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Invalid livelihood pathway."
        }), 400


    if int(vacancies) < 1:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "At least one vacancy is required."
        }), 400

    cursor.execute("""
        INSERT INTO jobs
        (
            title,
            duration,
            salary,
            location,
            description,
            status,
            posted_by,

            livelihood_path,
            wage_type,
            wage_amount,

            work_date,
            start_time,
            end_time,
            meeting_point,

            work_latitude,
            work_longitude,
            meeting_latitude,
            meeting_longitude,

            payment_commitment,
            payment_due_date,

            vacancies,
            requirements
        )
        VALUES
        (
            %s,%s,%s,%s,%s,'Open',%s,
            %s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,
            %s,%s
        )
    """, (
        title,
        data.get("duration"),
        data.get("salary"),
        location,
        description,
        employer_email,

        livelihood_path,
        wage_type,
        wage_amount,

        data.get("work_date"),
        data.get("start_time"),
        data.get("end_time"),
        data.get("meeting_point"),

        data.get("work_latitude"),
        data.get("work_longitude"),
        data.get("meeting_latitude"),
        data.get("meeting_longitude"),

        data.get(
            "payment_commitment",
            "END_OF_DAY"
        ),

        data.get("payment_due_date"),

        int(vacancies),
        data.get("requirements")
    ))

    job_id = cursor.lastrowid

    db.commit()

    cursor.close()
    db.close()

    add_notification(
        employer_email,
        "Job #" + str(job_id) +
        " has been posted successfully."
    )

    add_activity(
        employer_email,
        "Posted Job #" + str(job_id)
    )

    return jsonify({
        "success": True,
        "message": "Job posted successfully.",
        "job_id": job_id
    }), 201


# ------------------------------------------------------------
# APPLY FOR JOB
#
# Supports both:
#
# SELF    -> beneficiary applies themselves
# ASSISTED -> volunteer/NGO applies on behalf of beneficiary
#
# At this stage, the frontend will not use this API yet.
# ------------------------------------------------------------
@app.route('/apply_job', methods=['POST'])
def apply_job():

    data = request.get_json(silent=True) or {}

    job_id = data.get("job_id")
    beneficiary_id = data.get("beneficiary_id")

    application_source = data.get(
        "application_source",
        "SELF"
    )

    submitted_by_email = data.get(
        "submitted_by_email"
    )

    if not job_id:
        return jsonify({
            "success": False,
            "message": "Job ID is required."
        }), 400

    if not beneficiary_id:
        return jsonify({
            "success": False,
            "message": "Beneficiary ID is required."
        }), 400

    if application_source not in [
        "SELF",
        "ASSISTED"
    ]:
        return jsonify({
            "success": False,
            "message": "Invalid application source."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------------------------
    # CHECK JOB
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            title,
            status,
            vacancies
        FROM jobs
        WHERE id=%s
    """, (job_id,))

    job = cursor.fetchone()

    if not job:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Job not found."
        }), 404

    if job["status"] != "Open":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This job is no longer accepting applications."
        }), 400

    # --------------------------------------------------------
    # CHECK BENEFICIARY
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            full_name,
            phone,
            location,
            skills,
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

    # --------------------------------------------------------
    # ASSISTED APPLICATION
    # --------------------------------------------------------

    if application_source == "ASSISTED":

        if not submitted_by_email:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Volunteer or NGO email is required for assisted applications."
            }), 400

        cursor.execute("""
            SELECT
                email,
                role,
                status
            FROM users
            WHERE email=%s
        """, (submitted_by_email,))

        submitter = cursor.fetchone()

        if not submitter:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Submitting Volunteer/NGO account not found."
            }), 404

        if submitter["role"] not in [
            "Volunteer",
            "NGO"
        ]:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Only Volunteers or NGOs can submit assisted applications."
            }), 403

        if submitter["status"] != "Active":
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Submitting account is not active."
            }), 403


    # --------------------------------------------------------
    # SELF APPLICATION
    # --------------------------------------------------------

    if application_source == "SELF":

        if not submitted_by_email:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Beneficiary email is required for self applications."
            }), 400

        cursor.execute("""
            SELECT
                u.email,
                u.role,
                u.status,
                b.id AS beneficiary_id
            FROM users u
            INNER JOIN beneficiaries b
                ON b.user_id = u.id
            WHERE u.email=%s
        """, (submitted_by_email,))

        beneficiary_account = cursor.fetchone()

        if not beneficiary_account:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Beneficiary account not found."
            }), 404

        if beneficiary_account["role"] != "Beneficiary":
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Only beneficiary accounts can submit self applications."
            }), 403

        if beneficiary_account["status"] != "Active":
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Beneficiary account is not active."
            }), 403

        if int(beneficiary_account["beneficiary_id"]) != int(beneficiary_id):
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Beneficiary account does not match the selected profile."
            }), 403

    # --------------------------------------------------------
    # PREVENT DUPLICATE APPLICATION
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id
        FROM job_applications
        WHERE job_id=%s
        AND beneficiary_id=%s
        AND application_status NOT IN (
            'Rejected',
            'Withdrawn'
        )
        LIMIT 1
    """, (
        job_id,
        beneficiary_id
    ))

    existing = cursor.fetchone()

    if existing:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This beneficiary has already applied for this job."
        }), 409

    # --------------------------------------------------------
    # CREATE APPLICATION
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO job_applications
        (
            job_id,
            applicant_name,
            applicant_phone,
            applicant_skills,
            application_status,
            applicant_email,

            beneficiary_id,
            submitted_by_email,
            application_source
        )
        VALUES
        (
            %s,%s,%s,%s,
            'Pending',
            %s,%s,%s,%s
        )
    """, (
        job_id,
        beneficiary["full_name"],
        beneficiary["phone"],
        beneficiary["skills"],
        submitted_by_email,
        beneficiary_id,
        submitted_by_email,
        application_source
    ))

    application_id = cursor.lastrowid

    db.commit()

    # --------------------------------------------------------
    # GET EMPLOYER
    # --------------------------------------------------------

    cursor.execute("""
        SELECT posted_by
        FROM jobs
        WHERE id=%s
    """, (job_id,))

    employer = cursor.fetchone()

    cursor.close()
    db.close()

    # Notify employer
    if employer and employer["posted_by"]:

        add_notification(
            employer["posted_by"],
            "New application received for Job #" +
            str(job_id) + "."
        )

    # Notify submitter when assisted
    if application_source == "ASSISTED":

        add_notification(
            submitted_by_email,
            "Application submitted for " +
            beneficiary["full_name"] +
            " to Job #" +
            str(job_id) + "."
        )

        add_activity(
            submitted_by_email,
            "Applied for Job #" +
            str(job_id) +
            " on behalf of " +
            beneficiary["full_name"]
        )

    return jsonify({
        "success": True,
        "message": "Application submitted successfully.",
        "application_id": application_id
    }), 201


# ------------------------------------------------------------
# GET APPLICATIONS
#
# Admin can see all applications.
# Employer can later use the same API with employer_email
# to see applications only for their own jobs.
# ------------------------------------------------------------
# ------------------------------------------------------------
# GET APPLICATIONS
# ------------------------------------------------------------

@app.route('/get_applications', methods=['GET'])
def get_applications():

    email = request.args.get("email")


    if not email:

        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # VERIFY USER
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        email,
    ))

    user = cursor.fetchone()


    if not user:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404


    if user["status"] != "Active":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Account is not active."
        }), 403


    role = user["role"]


    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if role == "Admin":

        cursor.execute("""
            SELECT

                ja.id,
                ja.job_id,
                ja.beneficiary_id,

                ja.applicant_name,
                ja.applicant_phone,
                ja.applicant_skills,
                ja.applicant_email,

                ja.application_status,
                ja.applied_at,

                ja.application_source,
                ja.submitted_by_email,

                ja.shortlisted_at,
                ja.rejected_at,

                j.title AS job_title,
                j.location AS job_location,
                j.work_date,
                j.wage_type,
                j.wage_amount,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,
                b.education AS beneficiary_education,
                b.skills AS beneficiary_skills,
                b.experience_years AS beneficiary_experience,
                b.availability AS beneficiary_availability,
                b.preferred_work_type

            FROM job_applications ja

            INNER JOIN jobs j
                ON j.id = ja.job_id

            LEFT JOIN beneficiaries b
                ON b.id = ja.beneficiary_id

            ORDER BY ja.id DESC

        """)


    # --------------------------------------------------------
    # EMPLOYER
    # --------------------------------------------------------

    elif role == "Employer":

        cursor.execute("""
            SELECT

                ja.id,
                ja.job_id,
                ja.beneficiary_id,

                ja.applicant_name,
                ja.applicant_phone,
                ja.applicant_skills,
                ja.applicant_email,

                ja.application_status,
                ja.applied_at,

                ja.application_source,
                ja.submitted_by_email,

                ja.shortlisted_at,
                ja.rejected_at,

                j.title AS job_title,
                j.location AS job_location,
                j.work_date,
                j.wage_type,
                j.wage_amount,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,
                b.education AS beneficiary_education,
                b.skills AS beneficiary_skills,
                b.experience_years AS beneficiary_experience,
                b.availability AS beneficiary_availability,
                b.preferred_work_type

            FROM job_applications ja

            INNER JOIN jobs j
                ON j.id = ja.job_id

            LEFT JOIN beneficiaries b
                ON b.id = ja.beneficiary_id

            WHERE j.posted_by=%s

            ORDER BY ja.id DESC

        """, (
            email,
        ))


    # --------------------------------------------------------
    # BENEFICIARY
    # --------------------------------------------------------

    elif role == "Beneficiary":

        cursor.execute("""
            SELECT

                ja.id,
                ja.job_id,
                ja.beneficiary_id,

                ja.applicant_name,
                ja.applicant_phone,
                ja.applicant_skills,
                ja.applicant_email,

                ja.application_status,
                ja.applied_at,

                ja.application_source,
                ja.submitted_by_email,

                ja.shortlisted_at,
                ja.rejected_at,

                j.title AS job_title,
                j.location AS job_location,
                j.work_date,
                j.wage_type,
                j.wage_amount,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,
                b.education AS beneficiary_education,
                b.skills AS beneficiary_skills,
                b.experience_years AS beneficiary_experience,
                b.availability AS beneficiary_availability,
                b.preferred_work_type

            FROM job_applications ja

            INNER JOIN jobs j
                ON j.id = ja.job_id

            LEFT JOIN beneficiaries b
                ON b.id = ja.beneficiary_id

            WHERE ja.applicant_email=%s

            ORDER BY ja.id DESC

        """, (
            email,
        ))


    # --------------------------------------------------------
    # VOLUNTEER / NGO
    # --------------------------------------------------------

    elif role in [
        "Volunteer",
        "NGO"
    ]:

        cursor.execute("""
            SELECT

                ja.id,
                ja.job_id,
                ja.beneficiary_id,

                ja.applicant_name,
                ja.applicant_phone,
                ja.applicant_skills,
                ja.applicant_email,

                ja.application_status,
                ja.applied_at,

                ja.application_source,
                ja.submitted_by_email,

                ja.shortlisted_at,
                ja.rejected_at,

                j.title AS job_title,
                j.location AS job_location,
                j.work_date,
                j.wage_type,
                j.wage_amount,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,
                b.education AS beneficiary_education,
                b.skills AS beneficiary_skills,
                b.experience_years AS beneficiary_experience,
                b.availability AS beneficiary_availability,
                b.preferred_work_type

            FROM job_applications ja

            INNER JOIN jobs j
                ON j.id = ja.job_id

            LEFT JOIN beneficiaries b
                ON b.id = ja.beneficiary_id

            WHERE ja.submitted_by_email=%s

            AND ja.application_source='ASSISTED'

        """, (
            email,
        ))


    else:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Unauthorized role."
        }), 403


    applications = cursor.fetchall()


    cursor.close()
    db.close()


    # --------------------------------------------------------
    # FORMAT DATES
    # --------------------------------------------------------

    for application in applications:

        for field in [
            "applied_at",
            "shortlisted_at",
            "rejected_at"
        ]:

            if application.get(field):

                application[field] = (
                    application[field]
                    .strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )
                )


        if application.get("work_date"):

            application["work_date"] = (
                application["work_date"]
                .strftime(
                    "%Y-%m-%d"
                )
            )


    return jsonify({
        "success": True,
        "applications": applications
    })
    

# ------------------------------------------------------------
# SHORTLIST APPLICATION
# ------------------------------------------------------------
@app.route('/shortlist_application/<int:application_id>', methods=['POST'])
def shortlist_application(application_id):

    data = request.get_json(silent=True) or {}

    employer_email = data.get("employer_email")

    if not employer_email:
        return jsonify({
            "success": False,
            "message": "Employer email is required."
        }), 400

    # --------------------------------------------------------
    # VERIFY EMPLOYER ACCOUNT
    # --------------------------------------------------------
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        employer_email,
    ))

    employer = cursor.fetchone()


    if not employer:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account not found."
        }), 404


    if employer["role"] != "Employer":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only employers can manage applications."
        }), 403


    if employer["status"] != "Active":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account is not active."
        }), 403


    # Verify employer owns the job
    cursor.execute("""
        SELECT
            ja.id,
            ja.application_status,
            j.id AS job_id,
            j.posted_by
        FROM job_applications ja

        INNER JOIN jobs j
            ON j.id = ja.job_id

        WHERE ja.id=%s
    """, (application_id,))

    application = cursor.fetchone()

    if not application:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Application not found."
        }), 404

    if application["posted_by"] != employer_email:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not authorized to manage this application."
        }), 403

    if application["application_status"] != "Pending":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only pending applications can be shortlisted."
        }), 400

    cursor.execute("""
        UPDATE job_applications
        SET
            application_status='Shortlisted',
            shortlisted_at=NOW()
        WHERE id=%s
    """, (application_id,))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "message": "Applicant shortlisted successfully."
    })


# ------------------------------------------------------------
# REJECT APPLICATION
# ------------------------------------------------------------
@app.route('/reject_application/<int:application_id>', methods=['POST'])
def reject_application(application_id):

    data = request.get_json(silent=True) or {}

    employer_email = data.get(
        "employer_email"
    )


    if not employer_email:
        return jsonify({
            "success": False,
            "message": "Employer email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------------------------
    # VERIFY EMPLOYER ACCOUNT
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        employer_email,
    ))

    employer = cursor.fetchone()


    if not employer:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account not found."
        }), 404


    if employer["role"] != "Employer":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only employers can manage applications."
        }), 403


    if employer["status"] != "Active":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account is not active."
        }), 403


    cursor.execute("""
        SELECT
            ja.id,
            ja.application_status,
            j.posted_by
        FROM job_applications ja

        INNER JOIN jobs j
            ON j.id = ja.job_id

        WHERE ja.id=%s
    """, (application_id,))

    application = cursor.fetchone()

    if not application:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Application not found."
        }), 404

    if application["posted_by"] != employer_email:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not authorized to manage this application."
        }), 403

    cursor.execute("""
        UPDATE job_applications
        SET
            application_status='Rejected',
            rejected_at=NOW()
        WHERE id=%s
    """, (application_id,))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "message": "Application rejected."
    })


# ------------------------------------------------------------
# SEND JOB OFFER
# ------------------------------------------------------------
@app.route('/send_job_offer', methods=['POST'])
def send_job_offer():

    data = request.get_json(silent=True) or {}

    application_id = data.get("application_id")
    employer_email = data.get("employer_email")

    if not application_id or not employer_email:
        return jsonify({
            "success": False,
            "message": "Application ID and employer email are required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------------------------
    # VERIFY EMPLOYER ACCOUNT
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        employer_email,
    ))

    employer = cursor.fetchone()

    if not employer:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account not found."
        }), 404

    if employer["role"] != "Employer":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only employers can send job offers."
        }), 403

    if employer["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account is not active."
        }), 403

    cursor.execute("""
        SELECT
            ja.id,
            ja.job_id,
            ja.beneficiary_id,
            ja.application_status,

            j.posted_by,
            j.title,
            j.wage_type,
            j.wage_amount,
            j.payment_commitment,

            b.full_name AS beneficiary_name

        FROM job_applications ja

        INNER JOIN jobs j
            ON j.id = ja.job_id

        INNER JOIN beneficiaries b
            ON b.id = ja.beneficiary_id

        WHERE ja.id=%s
    """, (application_id,))

    application = cursor.fetchone()

    if not application:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Application not found."
        }), 404

    if application["posted_by"] != employer_email:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not authorized to send this offer."
        }), 403

    if application["application_status"] != "Shortlisted":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only shortlisted applicants can receive a job offer."
        }), 400

    # Prevent duplicate active offers
    cursor.execute("""
        SELECT id
        FROM job_offers
        WHERE application_id=%s
        AND status='SENT'
        LIMIT 1
    """, (application_id,))

    existing_offer = cursor.fetchone()

    if existing_offer:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "An active offer already exists for this application."
        }), 409

    offered_wage = data.get(
        "offered_wage",
        application["wage_amount"]
    )

    payment_commitment = data.get(
        "payment_commitment",
        application["payment_commitment"]
    )

    offer_message = data.get("offer_message")

    cursor.execute("""
        INSERT INTO job_offers
        (
            application_id,
            job_id,
            beneficiary_id,
            employer_email,
            offered_wage,
            payment_commitment,
            offer_message
        )
        VALUES(%s,%s,%s,%s,%s,%s,%s)
    """, (
        application_id,
        application["job_id"],
        application["beneficiary_id"],
        employer_email,
        offered_wage,
        payment_commitment,
        offer_message
    ))

    offer_id = cursor.lastrowid

    cursor.execute("""
        UPDATE job_applications
        SET application_status='Selected'
        WHERE id=%s
    """, (application_id,))

    db.commit()

    cursor.close()
    db.close()

    # If beneficiary has no direct account yet,
    # notification will be handled through assisted access.
    add_notification(
        employer_email,
        "Job offer sent for " +
        application["beneficiary_name"] +
        " - Job #" +
        str(application["job_id"])
    )

    return jsonify({
        "success": True,
        "message": "Job offer sent successfully.",
        "offer_id": offer_id
    }), 201



# ============================================================
# GET JOB OFFERS FOR BENEFICIARY
# ============================================================

@app.route('/get_job_offers', methods=['GET'])
def get_job_offers():

    email = request.args.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------------------------
    # FIND SELF-ACCESS BENEFICIARY
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            b.id AS beneficiary_id,
            b.full_name,
            b.digital_access_mode
        FROM beneficiaries b

        INNER JOIN users u
            ON u.id = b.user_id

        WHERE u.email=%s
        AND u.role='Beneficiary'
        AND u.status='Active'
    """, (email,))

    beneficiary = cursor.fetchone()

    if not beneficiary:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "No beneficiary profile is linked to this account."
        }), 404

    cursor.execute("""
        SELECT
            jo.id AS offer_id,
            jo.application_id,
            jo.job_id,
            jo.beneficiary_id,

            jo.employer_email,
            jo.offered_wage,
            jo.payment_commitment,
            jo.offer_message,
            jo.status AS offer_status,
            jo.sent_at,

            j.title AS job_title,
            j.location AS job_location,
            j.meeting_point,
            j.work_date,
            j.start_time,
            j.end_time,
            j.description,

            u.name AS employer_name

        FROM job_offers jo

        INNER JOIN jobs j
            ON j.id = jo.job_id

        LEFT JOIN users u
            ON u.email = jo.employer_email

        WHERE jo.beneficiary_id=%s
        AND jo.status='SENT'

        ORDER BY jo.sent_at DESC
    """, (
        beneficiary["beneficiary_id"],
    ))

    offers = cursor.fetchall()

    cursor.close()
    db.close()

    for offer in offers:

        if offer["sent_at"]:
            offer["sent_at"] = (
                offer["sent_at"]
                .strftime("%Y-%m-%dT%H:%M:%S")
            )

        if offer["work_date"]:
            offer["work_date"] = (
                offer["work_date"]
                .strftime("%Y-%m-%d")
            )

        if offer["start_time"]:
            offer["start_time"] = str(
                offer["start_time"]
            )

        if offer["end_time"]:
            offer["end_time"] = str(
                offer["end_time"]
            )

    return jsonify({
        "success": True,
        "offers": offers
    })



# ============================================================
# GET ASSISTED JOB OFFERS
#
# Used by Volunteer / NGO / Admin to view offers belonging
# to beneficiaries who may not have direct smartphone access.
# ============================================================
@app.route('/get_assisted_job_offers', methods=['GET'])
def get_assisted_job_offers():

    responder_email = request.args.get(
        "responder_email"
    )

    if not responder_email:

        return jsonify({
            "success": False,
            "message": "Responder email is required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # VERIFY RESPONDER
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        responder_email,
    ))

    responder = cursor.fetchone()


    if not responder:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Responder account not found."
        }), 404


    if responder["role"] not in [
        "Volunteer",
        "NGO",
        "Admin"
    ]:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only Volunteer, NGO or Admin can view assisted offers."
        }), 403


    if responder["status"] != "Active":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Responder account is not active."
        }), 403


    # --------------------------------------------------------
    # GET ASSISTED OFFERS
    # --------------------------------------------------------
    if responder["role"] == "Admin":

        cursor.execute("""
            SELECT
                jo.id AS offer_id,
                jo.application_id,
                jo.job_id,
                jo.beneficiary_id,

                jo.employer_email,
                jo.offered_wage,
                jo.payment_commitment,
                jo.offer_message,

                jo.status AS offer_status,
                jo.sent_at,

                j.title AS job_title,
                j.location AS job_location,
                j.meeting_point,

                j.work_date,
                j.start_time,
                j.end_time,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,

                u.name AS employer_name

            FROM job_offers jo

            INNER JOIN job_applications ja
                ON ja.id = jo.application_id

            INNER JOIN jobs j
                ON j.id = jo.job_id

            INNER JOIN beneficiaries b
                ON b.id = jo.beneficiary_id

            LEFT JOIN users u
                ON u.email = jo.employer_email

            WHERE jo.status='SENT'

            AND (
                b.digital_access_mode='ASSISTED'
                OR b.user_id IS NULL
            )

            AND ja.application_source='ASSISTED'

            ORDER BY jo.sent_at DESC
        """)

    else:

        cursor.execute("""
            SELECT
                jo.id AS offer_id,
                jo.application_id,
                jo.job_id,
                jo.beneficiary_id,

                jo.employer_email,
                jo.offered_wage,
                jo.payment_commitment,
                jo.offer_message,

                jo.status AS offer_status,
                jo.sent_at,

                j.title AS job_title,
                j.location AS job_location,
                j.meeting_point,

                j.work_date,
                j.start_time,
                j.end_time,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,

                u.name AS employer_name

            FROM job_offers jo

            INNER JOIN job_applications ja
                ON ja.id = jo.application_id

            INNER JOIN jobs j
                ON j.id = jo.job_id

            INNER JOIN beneficiaries b
                ON b.id = jo.beneficiary_id

            LEFT JOIN users u
                ON u.email = jo.employer_email

            WHERE jo.status='SENT'

            AND (
                b.digital_access_mode='ASSISTED'
                OR b.user_id IS NULL
            )

            AND ja.application_source='ASSISTED'

            AND ja.submitted_by_email=%s

            ORDER BY jo.sent_at DESC
        """, (
            responder_email,
        ))

    offers = cursor.fetchall()

    cursor.close()
    db.close()


    for offer in offers:
        if offer["sent_at"]:
            offer["sent_at"] = (
                offer["sent_at"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )

        if offer["work_date"]:
            offer["work_date"] = (
                offer["work_date"]
                .strftime(
                    "%Y-%m-%d"
                )
            )

        if offer["start_time"]:
            offer["start_time"] = str(
                offer["start_time"]
            )

        if offer["end_time"]:
            offer["end_time"] = str(
                offer["end_time"]
            )

    return jsonify({
        "success": True,
        "offers": offers
    })


# ============================================================
# RESPOND TO JOB OFFER
#
# SELF:
# Beneficiary responds using their own account.
#
# ASSISTED:
# Authorized Volunteer/NGO responds on behalf of beneficiary.
# ============================================================
@app.route('/respond_job_offer', methods=['POST'])
def respond_job_offer():

    data = request.get_json(silent=True) or {}

    offer_id = data.get("offer_id")
    response = data.get("response")
    response_mode = data.get(
        "response_mode",
        "SELF"
    )
    responder_email = data.get(
        "responder_email"
    )

    if not offer_id:
        return jsonify({
            "success": False,
            "message": "Offer ID is required."
        }), 400

    if response not in [
        "ACCEPTED",
        "DECLINED"
    ]:
        return jsonify({
            "success": False,
            "message": "Response must be ACCEPTED or DECLINED."
        }), 400

    if response_mode not in [
        "SELF",
        "ASSISTED"
    ]:
        return jsonify({
            "success": False,
            "message": "Invalid response mode."
        }), 400

    if not responder_email:
        return jsonify({
            "success": False,
            "message": "Responder email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------------------------
    # GET OFFER
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            jo.id,
            jo.application_id,
            jo.job_id,
            jo.beneficiary_id,
            jo.employer_email,
            jo.offered_wage,
            jo.payment_commitment,
            jo.status,

            j.title,
            j.location,
            j.meeting_point,
            j.work_date,
            j.start_time,
            j.end_time,

            b.full_name AS beneficiary_name,
            b.user_id AS beneficiary_user_id

        FROM job_offers jo

        INNER JOIN jobs j
            ON j.id = jo.job_id

        INNER JOIN beneficiaries b
            ON b.id = jo.beneficiary_id

        WHERE jo.id=%s
    """, (offer_id,))

    offer = cursor.fetchone()

    if not offer:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Job offer not found."
        }), 404

    if offer["status"] != "SENT":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This job offer has already been responded to."
        }), 409

    # --------------------------------------------------------
    # VERIFY RESPONDER
    # --------------------------------------------------------
    if response_mode == "SELF":

        cursor.execute("""
            SELECT
                id,
                email,
                role,
                status
            FROM users
            WHERE email=%s
        """, (responder_email,))

        user = cursor.fetchone()

        if not user:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Beneficiary account not found."
            }), 404

        if user["role"] != "Beneficiary":
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Only the beneficiary can accept this offer directly."
            }), 403

        if user["status"] != "Active":
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Beneficiary account is not active."
            }), 403

        if user["id"] != offer["beneficiary_user_id"]:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "This offer does not belong to this beneficiary."
            }), 403

    # --------------------------------------------------------
    # ASSISTED RESPONSE
    # --------------------------------------------------------
    else:

        cursor.execute("""
            SELECT
                email,
                role,
                status
            FROM users
            WHERE email=%s
        """, (responder_email,))

        responder = cursor.fetchone()

        if not responder:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Responder account not found."
            }), 404

        if responder["role"] not in [
            "Volunteer",
            "NGO",
            "Admin"
        ]:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Only Volunteer, NGO or Admin can record an assisted response."
            }), 403

        if responder["status"] != "Active":
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Responder account is not active."
            }), 403


        # ----------------------------------------------------
        # VERIFY ASSISTED APPLICATION RELATIONSHIP
        # ----------------------------------------------------
        cursor.execute("""
            SELECT
                application_source,
                submitted_by_email
            FROM job_applications
            WHERE id=%s
        """, (
            offer["application_id"],
        ))

        application_info = cursor.fetchone()


        if not application_info:

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Application not found."
            }), 404


        if (
            application_info["application_source"]
            != "ASSISTED"
        ):

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "This offer is not an assisted application."
            }), 403


        if (
            application_info["submitted_by_email"]
            != responder_email
        ):

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "You are not authorized to respond to this assisted offer."
            }), 403

    # --------------------------------------------------------
    # DECLINED
    # --------------------------------------------------------
    if response == "DECLINED":

        cursor.execute("""
            UPDATE job_offers
            SET
                status='DECLINED',
                responded_at=NOW()
            WHERE id=%s
        """, (offer_id,))

        cursor.execute("""
            UPDATE job_applications
            SET application_status='Offer Declined'
            WHERE id=%s
        """, (
            offer["application_id"],
        ))

        db.commit()

        cursor.close()
        db.close()

        add_notification(
            offer["employer_email"],
            offer["beneficiary_name"] +
            " declined the job offer for Job #" +
            str(offer["job_id"])
        )

        if response_mode == "ASSISTED":

            add_activity(
                responder_email,
                "Recorded declined job offer for " +
                offer["beneficiary_name"]
            )

        return jsonify({
            "success": True,
            "message": "Job offer declined."
        })

    # --------------------------------------------------------
    # ACCEPTED
    # --------------------------------------------------------
    cursor.execute("""
        SELECT id
        FROM job_assignments
        WHERE offer_id=%s
        LIMIT 1
    """, (offer_id,))

    existing_assignment = cursor.fetchone()

    if existing_assignment:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This offer already has an assignment."
        }), 409


    # --------------------------------------------------------
    # CHECK JOB VACANCIES
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            j.vacancies,
            (
                SELECT COUNT(*)
                FROM job_assignments ja
                WHERE ja.job_id = j.id
                AND ja.status NOT IN (
                    'CANCELLED',
                    'REJECTED'
                )
            ) AS filled_vacancies

        FROM jobs j

        WHERE j.id=%s

        FOR UPDATE
    """, (
        offer["job_id"],
    ))

    vacancy_info = cursor.fetchone()

    if not vacancy_info:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Job not found."
        }), 404


    if (
        vacancy_info["vacancies"] is not None
        and
        vacancy_info["filled_vacancies"]
        >= vacancy_info["vacancies"]
    ):

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "All vacancies for this job have already been filled."
        }), 409


    # --------------------------------------------------------
    # CREATE ASSIGNMENT
    # --------------------------------------------------------
    cursor.execute("""
        INSERT INTO job_assignments
        (
            job_id,
            application_id,
            offer_id,

            beneficiary_id,
            employer_email,

            work_date,

            work_location,
            meeting_point,

            agreed_wage,
            wage_type,

            payment_commitment,

            status,
            accepted_at
        )
        SELECT
            jo.job_id,
            jo.application_id,
            jo.id,

            jo.beneficiary_id,
            jo.employer_email,

            j.work_date,

            j.location,
            j.meeting_point,

            jo.offered_wage,
            j.wage_type,

            jo.payment_commitment,

            'ASSIGNED',
            NOW()

        FROM job_offers jo

        INNER JOIN jobs j
            ON j.id = jo.job_id

        WHERE jo.id=%s
    """, (offer_id,))

    assignment_id = cursor.lastrowid


    # --------------------------------------------------------
    # UPDATE OFFER
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE job_offers
        SET
            status='ACCEPTED',
            responded_at=NOW()
        WHERE id=%s
    """, (offer_id,))

    # --------------------------------------------------------
    # UPDATE APPLICATION
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE job_applications
        SET application_status='Offer Accepted'
        WHERE id=%s
    """, (
        offer["application_id"],
    ))

    db.commit()

    cursor.close()
    db.close()

    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    add_notification(
        offer["employer_email"],
        offer["beneficiary_name"] +
        " accepted the job offer for Job #" +
        str(offer["job_id"])
    )

    if response_mode == "ASSISTED":

        add_activity(
            responder_email,
            "Accepted job offer on behalf of " +
            offer["beneficiary_name"]
        )

    if offer["beneficiary_user_id"]:

        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)

        cursor2.execute("""
            SELECT email
            FROM users
            WHERE id=%s
        """, (
            offer["beneficiary_user_id"],
        ))

        beneficiary_user = cursor2.fetchone()

        cursor2.close()
        db2.close()

        if beneficiary_user:

            add_notification(
                beneficiary_user["email"],
                "Your job offer has been accepted and your assignment is ready."
            )

    return jsonify({
        "success": True,
        "message": "Job offer accepted and assignment created successfully.",
        "assignment_id": assignment_id
    }), 201



# ============================================================
# GET JOB ASSIGNMENTS
#
# Supports:
# Employer
# Beneficiary
# Admin
# Volunteer / NGO
# ============================================================

@app.route('/get_job_assignments', methods=['GET'])
def get_job_assignments():

    email = request.args.get("email")

    if not email:

        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # VERIFY USER
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            email,
            name,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        email,
    ))

    user = cursor.fetchone()


    if not user:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404


    if user["status"] != "Active":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Account is not active."
        }), 403


    # --------------------------------------------------------
    # USE ROLE FROM DATABASE
    # --------------------------------------------------------
    role = user["role"]

    # --------------------------------------------------------
    # BUILD QUERY BASED ON ROLE
    # --------------------------------------------------------
    if role == "Employer":

        query = """
            SELECT

                ja.id AS assignment_id,

                ja.job_id,
                ja.application_id,
                ja.offer_id,

                ja.beneficiary_id,
                ja.employer_email,

                ja.work_date,
                ja.work_location,
                ja.meeting_point,

                ja.agreed_wage,
                ja.wage_type,

                ja.payment_commitment,

                ja.status,
                ja.accepted_at,

                j.title AS job_title,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location

            FROM job_assignments ja

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = ja.beneficiary_id

            WHERE ja.employer_email=%s

            ORDER BY
                ja.work_date ASC,
                ja.accepted_at DESC
        """

        params = (
            email,
        )


    elif role == "Beneficiary":

        query = """
            SELECT

                ja.id AS assignment_id,

                ja.job_id,
                ja.application_id,
                ja.offer_id,

                ja.beneficiary_id,
                ja.employer_email,

                ja.work_date,
                ja.work_location,
                ja.meeting_point,

                ja.agreed_wage,
                ja.wage_type,

                ja.payment_commitment,

                ja.status,
                ja.accepted_at,

                j.title AS job_title,

                u.name AS employer_name,
                u.email AS employer_contact

            FROM job_assignments ja

            INNER JOIN jobs j
                ON j.id = ja.job_id

            LEFT JOIN users u
                ON u.email = ja.employer_email

            INNER JOIN beneficiaries b
                ON b.id = ja.beneficiary_id

            INNER JOIN users bu
                ON bu.id = b.user_id

            WHERE bu.email=%s

            ORDER BY
                ja.work_date ASC,
                ja.accepted_at DESC
        """

        params = (
            email,
        )


    elif role == "Admin":
        query = """
            SELECT

                ja.id AS assignment_id,

                ja.job_id,
                ja.application_id,
                ja.offer_id,

                ja.beneficiary_id,
                ja.employer_email,

                ja.work_date,
                ja.work_location,
                ja.meeting_point,

                ja.agreed_wage,
                ja.wage_type,

                ja.payment_commitment,

                ja.status,
                ja.accepted_at,

                j.title AS job_title,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,

                u.name AS employer_name

            FROM job_assignments ja

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = ja.beneficiary_id

            LEFT JOIN users u
                ON u.email = ja.employer_email

            ORDER BY
                ja.work_date ASC,
                ja.accepted_at DESC
        """

        params = ()


    elif role in [
        "Volunteer",
        "NGO"
    ]:

        query = """
            SELECT
                ja.id AS assignment_id,
                ja.job_id,
                ja.application_id,
                ja.offer_id,

                ja.beneficiary_id,
                ja.employer_email,

                ja.work_date,
                ja.work_location,
                ja.meeting_point,

                ja.agreed_wage,
                ja.wage_type,
                ja.payment_commitment,

                ja.status,
                ja.accepted_at,

                j.title AS job_title,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,

                u.name AS employer_name

            FROM job_assignments ja

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = ja.beneficiary_id

            LEFT JOIN users u
                ON u.email = ja.employer_email

            WHERE ja.application_id IN (
                SELECT id
                FROM job_applications
                WHERE application_source='ASSISTED'
                AND submitted_by_email=%s
            )

            ORDER BY
                ja.work_date ASC,
                ja.accepted_at DESC
        """
        params = (
            email,
        )

    else:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Unauthorized role."
        }), 403


    cursor.execute(
        query,
        params
    )

    assignments = cursor.fetchall()


    cursor.close()
    db.close()


    # --------------------------------------------------------
    # FORMAT DATES
    # --------------------------------------------------------

    for assignment in assignments:

        if assignment.get(
            "work_date"
        ):

            assignment["work_date"] = (
                assignment["work_date"]
                .strftime("%Y-%m-%d")
            )


        if assignment.get(
            "accepted_at"
        ):

            assignment["accepted_at"] = (
                assignment["accepted_at"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )


    return jsonify({

        "success": True,

        "assignments":
            assignments

    })



# ============================================================
# START WORK SESSION
# ============================================================

@app.route('/start_work_session', methods=['POST'])
def start_work_session():

    data = request.get_json(silent=True) or {}

    assignment_id = data.get("assignment_id")
    employer_email = data.get("employer_email")

    if not assignment_id or not employer_email:

        return jsonify({
            "success": False,
            "message": "Assignment ID and employer email are required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # VERIFY ASSIGNMENT
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            ja.id,
            ja.beneficiary_id,
            ja.employer_email,
            ja.work_date,
            ja.status

        FROM job_assignments ja

        WHERE ja.id=%s
    """, (
        assignment_id,
    ))

    assignment = cursor.fetchone()


    if not assignment:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Job assignment not found."
        }), 404


    if assignment["employer_email"] != employer_email:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not authorized to manage this assignment."
        }), 403


    if assignment["status"] != "ASSIGNED":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This assignment is not available for work."
        }), 409


    # --------------------------------------------------------
    # CHECK EXISTING SESSION
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            attendance_status,
            work_status

        FROM work_sessions

        WHERE assignment_id=%s
        AND work_date=%s
    """, (
        assignment_id,
        assignment["work_date"]
    ))

    existing_session = cursor.fetchone()


    if existing_session:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "A work session already exists for this assignment and date."
        }), 409


    # --------------------------------------------------------
    # CREATE SESSION
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO work_sessions
        (
            assignment_id,
            beneficiary_id,
            employer_email,
            work_date,
            start_time,
            attendance_status,
            work_status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            NOW(),
            'PRESENT',
            'IN_PROGRESS'
        )
    """, (
        assignment_id,
        assignment["beneficiary_id"],
        employer_email,
        assignment["work_date"]
    ))


    session_id = cursor.lastrowid


    # --------------------------------------------------------
    # UPDATE ASSIGNMENT
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE job_assignments
        SET status='IN_PROGRESS'
        WHERE id=%s
    """, (
        assignment_id,
    ))


    db.commit()

    cursor.close()
    db.close()


    return jsonify({
        "success": True,
        "message": "Work session started successfully.",
        "session_id": session_id
    }), 201


# ============================================================
# COMPLETE WORK SESSION
# ============================================================

@app.route('/complete_work_session', methods=['POST'])
def complete_work_session():

    data = request.get_json(silent=True) or {}

    session_id = data.get("session_id")
    employer_email = data.get("employer_email")
    hours_worked = data.get("hours_worked")
    employer_notes = data.get("employer_notes", "")

    if not session_id or not employer_email:

        return jsonify({
            "success": False,
            "message": "Session ID and employer email are required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # GET SESSION
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            ws.id,
            ws.assignment_id,
            ws.beneficiary_id,
            ws.work_date,
            ws.work_status,
            ws.attendance_status,

            ja.employer_email

        FROM work_sessions ws

        INNER JOIN job_assignments ja
            ON ja.id = ws.assignment_id

        WHERE ws.id=%s
    """, (
        session_id,
    ))

    session = cursor.fetchone()


    if not session:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Work session not found."
        }), 404


    if session["employer_email"] != employer_email:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not authorized to complete this work session."
        }), 403


    if session["work_status"] != "IN_PROGRESS":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This work session is not currently in progress."
        }), 409


    # --------------------------------------------------------
    # VALIDATE HOURS
    # --------------------------------------------------------

    if hours_worked is not None:

        try:

            hours_worked = float(hours_worked)

        except (TypeError, ValueError):

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Invalid hours worked."
            }), 400


        if hours_worked < 0 or hours_worked > 24:

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Hours worked must be between 0 and 24."
            }), 400

    else:

        hours_worked = None


    # --------------------------------------------------------
    # COMPLETE SESSION
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE work_sessions
        SET
            end_time=NOW(),
            hours_worked=%s,
            attendance_status='PRESENT',
            work_status='COMPLETED',
            employer_notes=%s
        WHERE id=%s
    """, (
        hours_worked,
        employer_notes,
        session_id
    ))


    # --------------------------------------------------------
    # UPDATE ASSIGNMENT
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE job_assignments
        SET status='WORK_COMPLETED'
        WHERE id=%s
    """, (
        session["assignment_id"],
    ))


    db.commit()

    cursor.close()
    db.close()


    return jsonify({
        "success": True,
        "message": "Work session completed successfully."
    })


# ============================================================
# CALCULATE WAGE FOR COMPLETED WORK
# ============================================================

@app.route('/calculate_wage', methods=['POST'])
def calculate_wage():

    data = request.get_json(silent=True) or {}

    session_id = data.get("session_id")
    employer_email = data.get("employer_email")

    if not session_id or not employer_email:

        return jsonify({
            "success": False,
            "message": "Session ID and employer email are required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # GET COMPLETED SESSION + ASSIGNMENT
    # --------------------------------------------------------

    cursor.execute("""
        SELECT

            ws.id AS session_id,
            ws.assignment_id,
            ws.beneficiary_id,
            ws.work_date,
            ws.hours_worked,
            ws.work_status,

            ja.employer_email,
            ja.agreed_wage,
            ja.wage_type

        FROM work_sessions ws

        INNER JOIN job_assignments ja
            ON ja.id = ws.assignment_id

        WHERE ws.id=%s

    """, (
        session_id,
    ))

    session = cursor.fetchone()


    if not session:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Work session not found."
        }), 404


    # --------------------------------------------------------
    # VERIFY EMPLOYER
    # --------------------------------------------------------

    if session["employer_email"] != employer_email:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not authorized to calculate this wage."
        }), 403


    # --------------------------------------------------------
    # WORK MUST BE COMPLETED
    # --------------------------------------------------------

    if session["work_status"] != "COMPLETED":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Wage can only be calculated after work is completed."
        }), 409


    # --------------------------------------------------------
    # PREVENT DUPLICATE WAGE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id
        FROM wage_records
        WHERE work_session_id=%s
        LIMIT 1
    """, (
        session_id,
    ))

    existing_wage = cursor.fetchone()


    if existing_wage:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Wage has already been calculated for this work session."
        }), 409


    # --------------------------------------------------------
    # CALCULATE WAGE
    # --------------------------------------------------------

    agreed_wage = float(
        session["agreed_wage"]
    )

    hours_worked = session["hours_worked"]


    if session["wage_type"] == "HOURLY":

        if hours_worked is None:

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Hours worked are required for hourly wages."
            }), 400


        wage_earned = (
            agreed_wage *
            float(hours_worked)
        )

    else:

        # DAILY wage

        wage_earned = agreed_wage


    # --------------------------------------------------------
    # CREATE WAGE RECORD
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO wage_records
        (
            assignment_id,
            work_session_id,
            beneficiary_id,
            employer_email,
            work_date,
            agreed_daily_wage,
            hours_worked,
            wage_earned,
            wage_status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            'DUE'
        )
    """, (
        session["assignment_id"],
        session["session_id"],
        session["beneficiary_id"],
        session["employer_email"],
        session["work_date"],
        agreed_wage,
        hours_worked,
        wage_earned
    ))


    wage_id = cursor.lastrowid


    # --------------------------------------------------------
    # UPDATE ASSIGNMENT
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE job_assignments
        SET status='PAYMENT_DUE'
        WHERE id=%s
    """, (
        session["assignment_id"],
    ))


    db.commit()

    cursor.close()
    db.close()


    return jsonify({
        "success": True,
        "message": "Wage calculated successfully.",
        "wage_id": wage_id,
        "wage_earned": wage_earned,
        "wage_status": "DUE"
    }), 201


# ============================================================
# RECORD PAYMENT
# ============================================================

@app.route('/record_payment', methods=['POST'])
def record_payment():

    data = request.get_json(silent=True) or {}

    wage_id = data.get("wage_id")
    employer_email = data.get("employer_email")

    payment_method = data.get(
        "payment_method"
    )

    transaction_reference = data.get(
        "transaction_reference"
    )

    notes = data.get(
        "notes",
        ""
    )


    if not wage_id or not employer_email:

        return jsonify({
            "success": False,
            "message": "Wage ID and employer email are required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # GET WAGE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT

            wr.id AS wage_id,
            wr.assignment_id,
            wr.work_session_id,
            wr.beneficiary_id,
            wr.employer_email,
            wr.wage_earned,
            wr.wage_status

        FROM wage_records wr

        WHERE wr.id=%s

    """, (
        wage_id,
    ))

    wage = cursor.fetchone()


    if not wage:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Wage record not found."
        }), 404


    # --------------------------------------------------------
    # VERIFY EMPLOYER
    # --------------------------------------------------------

    if wage["employer_email"] != employer_email:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not authorized to record this payment."
        }), 403


    # --------------------------------------------------------
    # WAGE MUST BE DUE
    # --------------------------------------------------------

    if wage["wage_status"] != "DUE":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "This wage is not currently due."
        }), 409


    # --------------------------------------------------------
    # CHECK DUPLICATE PAYMENT
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id
        FROM payments
        WHERE wage_record_id=%s
        LIMIT 1
    """, (
        wage_id,
    ))

    existing_payment = cursor.fetchone()


    if existing_payment:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "A payment record already exists for this wage."
        }), 409


    # --------------------------------------------------------
    # CREATE PAYMENT RECORD
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO payments
        (
            wage_record_id,
            assignment_id,
            work_session_id,
            beneficiary_id,
            employer_email,
            amount,
            payment_method,
            payment_status,
            payment_date,
            employer_confirmation,
            transaction_reference,
            notes
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            'PAID',
            NOW(),
            'CONFIRMED',
            %s,
            %s
        )
    """, (
        wage["wage_id"],
        wage["assignment_id"],
        wage["work_session_id"],
        wage["beneficiary_id"],
        wage["employer_email"],
        wage["wage_earned"],
        payment_method,
        transaction_reference,
        notes
    ))


    payment_id = cursor.lastrowid


    # --------------------------------------------------------
    # UPDATE WAGE
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE wage_records
        SET wage_status='PAID'
        WHERE id=%s
    """, (
        wage_id,
    ))


    # --------------------------------------------------------
    # UPDATE ASSIGNMENT
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE job_assignments
        SET status='PAID'
        WHERE id=%s
    """, (
        wage["assignment_id"],
    ))


    db.commit()

    cursor.close()
    db.close()


    return jsonify({
        "success": True,
        "message": "Payment recorded successfully.",
        "payment_id": payment_id,
        "amount": wage["wage_earned"],
        "payment_status": "PAID"
    }), 201



# ============================================================
# CONFIRM PAYMENT RECEIVED
# ============================================================

@app.route('/confirm_payment_received', methods=['POST'])
def confirm_payment_received():

    data = request.get_json(silent=True) or {}

    payment_id = data.get("payment_id")
    confirmation_mode = data.get(
        "confirmation_mode",
        "SELF"
    )
    responder_email = data.get(
        "responder_email"
    )

    if not payment_id or not responder_email:

        return jsonify({
            "success": False,
            "message": "Payment ID and responder email are required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # GET PAYMENT
    # --------------------------------------------------------

    cursor.execute("""
        SELECT

            p.id AS payment_id,
            p.wage_record_id,
            p.assignment_id,
            p.beneficiary_id,
            p.amount,
            p.payment_status,
            p.employer_confirmation,
            p.beneficiary_confirmation,

            b.user_id AS beneficiary_user_id

        FROM payments p

        INNER JOIN beneficiaries b
            ON b.id = p.beneficiary_id

        WHERE p.id=%s

    """, (
        payment_id,
    ))

    payment = cursor.fetchone()


    if not payment:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Payment record not found."
        }), 404


    # --------------------------------------------------------
    # PAYMENT MUST HAVE BEEN RECORDED BY EMPLOYER
    # --------------------------------------------------------

    if payment["payment_status"] != "PAID":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Payment has not yet been recorded by the employer."
        }), 409


    # --------------------------------------------------------
    # SELF CONFIRMATION
    # --------------------------------------------------------

    if confirmation_mode == "SELF":

        cursor.execute("""
            SELECT
                id,
                email,
                role,
                status
            FROM users
            WHERE email=%s
        """, (
            responder_email,
        ))

        responder = cursor.fetchone()


        if not responder:

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Beneficiary account not found."
            }), 404


        if responder["role"] != "Beneficiary":

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Only the beneficiary can confirm this payment."
            }), 403


        if responder["status"] != "Active":

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Beneficiary account is not active."
            }), 403


        if payment["beneficiary_user_id"] != responder["id"]:

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "You are not authorized to confirm this payment."
            }), 403


    # --------------------------------------------------------
    # ASSISTED CONFIRMATION
    # --------------------------------------------------------

    elif confirmation_mode == "ASSISTED":

        cursor.execute("""
            SELECT
                email,
                role,
                status
            FROM users
            WHERE email=%s
        """, (
            responder_email,
        ))

        responder = cursor.fetchone()


        if not responder:

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Responder account not found."
            }), 404


        if responder["role"] not in [
            "Volunteer",
            "NGO"
        ]:

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Only Volunteer or NGO can record assisted confirmation."
            }), 403


        if responder["status"] != "Active":

            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Responder account is not active."
            }), 403

        
        # ----------------------------------------------------
        # VERIFY ASSISTED APPLICATION RELATIONSHIP
        # ----------------------------------------------------
        cursor.execute("""
            SELECT
                ja.application_id
            FROM job_assignments ja
            INNER JOIN job_applications app
                ON app.id = ja.application_id
            WHERE ja.id=%s
            AND app.application_source='ASSISTED'
            AND app.submitted_by_email=%s
        """, (
            payment["assignment_id"],
            responder_email
        ))

        assisted_relation = cursor.fetchone()

        if not assisted_relation:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "You are not authorized to confirm this assisted payment."
            }), 403


    else:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Invalid confirmation mode."
        }), 400


    # --------------------------------------------------------
    # PREVENT DUPLICATE CONFIRMATION
    # --------------------------------------------------------

    if payment["beneficiary_confirmation"] == "CONFIRMED":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Payment has already been confirmed."
        }), 409


    # --------------------------------------------------------
    # CONFIRM PAYMENT
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE payments
        SET
            beneficiary_confirmation='CONFIRMED'
        WHERE id=%s
    """, (
        payment_id,
    ))


    # --------------------------------------------------------
    # MARK PAYMENT VERIFIED
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE payments
        SET
            payment_status='VERIFIED'
        WHERE id=%s
        AND employer_confirmation='CONFIRMED'
        AND beneficiary_confirmation='CONFIRMED'
    """, (
        payment_id,
    ))


    # --------------------------------------------------------
    # UPDATE WAGE
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE wage_records
        SET
            wage_status='VERIFIED'
        WHERE id=%s
        AND EXISTS (
            SELECT 1
            FROM payments p
            WHERE p.wage_record_id=wage_records.id
            AND p.payment_status='VERIFIED'
        )
    """, (
        payment["wage_record_id"],
    ))


    # --------------------------------------------------------
    # UPDATE ASSIGNMENT
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE job_assignments
        SET status='PAYMENT_VERIFIED'
        WHERE id=%s
        AND EXISTS (
            SELECT 1
            FROM payments p
            WHERE p.assignment_id=job_assignments.id
            AND p.payment_status='VERIFIED'
        )
    """, (
        payment["assignment_id"],
    ))


    db.commit()

    cursor.close()
    db.close()


    return jsonify({
        "success": True,
        "message": "Beneficiary payment confirmation recorded successfully."
    })



# ============================================================
# REPORT PAYMENT DISPUTE
# ============================================================
@app.route('/report_payment_dispute', methods=['POST'])
def report_payment_dispute():

    data = request.get_json(silent=True) or {}

    payment_id = data.get("payment_id")

    reported_by_email = data.get(
        "reported_by_email"
    )
    
    dispute_reason = data.get(
        "dispute_reason"
    )


    if (
        not payment_id
        or not reported_by_email
        or not dispute_reason
    ):

        return jsonify({
            "success": False,
            "message": "All dispute details are required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # GET PAYMENT
    # --------------------------------------------------------

    cursor.execute("""
        SELECT

            p.id AS payment_id,
            p.assignment_id,
            p.beneficiary_id,
            p.employer_email,
            p.payment_status

        FROM payments p

        WHERE p.id=%s

    """, (
        payment_id,
    ))

    payment = cursor.fetchone()


    if not payment:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Payment record not found."
        }), 404


    # --------------------------------------------------------
    # PAYMENT MUST NOT ALREADY BE VERIFIED
    # --------------------------------------------------------
    if payment["payment_status"] == "VERIFIED":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "A verified payment cannot be disputed."
        }), 409


    # --------------------------------------------------------
    # VERIFY RESPONDER
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        reported_by_email,
    ))

    user = cursor.fetchone()


    if not user:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404


    if user["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Account is not active."
        }), 403

    reported_by_role = user["role"]


    allowed_roles = [
        "Beneficiary",
        "Volunteer",
        "NGO",
        "Admin"
    ]


    if user["role"] not in allowed_roles:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "You are not authorized to report a payment dispute."
        }), 403


    # --------------------------------------------------------
    # VERIFY PAYMENT RELATIONSHIP
    # --------------------------------------------------------
    if user["role"] == "Beneficiary":
        cursor.execute("""
            SELECT id
            FROM beneficiaries
            WHERE id=%s
            AND user_id=%s
        """, (
            payment["beneficiary_id"],
            user["id"]
        ))

        beneficiary_relation = cursor.fetchone()

        if not beneficiary_relation:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "You are not authorized to dispute this payment."
            }), 403


    elif user["role"] in [
        "Volunteer",
        "NGO"
    ]:
        cursor.execute("""
            SELECT ja.id
            FROM job_assignments ja

            INNER JOIN job_applications app
                ON app.id = ja.application_id

            WHERE ja.id=%s
            AND app.application_source='ASSISTED'
            AND app.submitted_by_email=%s
        """, (
            payment["assignment_id"],
            reported_by_email
        ))

        assisted_relation = cursor.fetchone()

        if not assisted_relation:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "You are not authorized to dispute this payment."
            }), 403


    # --------------------------------------------------------
    # PREVENT DUPLICATE OPEN DISPUTES
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id
        FROM payment_disputes

        WHERE payment_id=%s

        AND dispute_status='OPEN'

        LIMIT 1

    """, (
        payment_id,
    ))

    existing_dispute = cursor.fetchone()


    if existing_dispute:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "An open dispute already exists for this payment."
        }), 409


    # --------------------------------------------------------
    # CREATE DISPUTE
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO payment_disputes
        (
            payment_id,
            assignment_id,
            beneficiary_id,
            employer_email,
            reported_by_email,
            reported_by_role,
            dispute_reason,
            dispute_status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            'OPEN'
        )
    """, (
        payment["payment_id"],
        payment["assignment_id"],
        payment["beneficiary_id"],
        payment["employer_email"],
        reported_by_email,
        reported_by_role,
        dispute_reason
    ))

    dispute_id = cursor.lastrowid

    # --------------------------------------------------------
    # UPDATE PAYMENT
    # --------------------------------------------------------
    cursor.execute("""
        UPDATE payments
        SET payment_status='DISPUTED'
        WHERE id=%s

    """, (
        payment_id,
    ))

    # --------------------------------------------------------
    # UPDATE WAGE
    # --------------------------------------------------------
    cursor.execute("""
        UPDATE wage_records wr

        INNER JOIN payments p
            ON p.wage_record_id = wr.id

        SET wr.wage_status='DISPUTED'

        WHERE p.id=%s

    """, (
        payment_id,
    ))


    # --------------------------------------------------------
    # UPDATE ASSIGNMENT
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE job_assignments ja

        INNER JOIN payments p
            ON p.assignment_id = ja.id

        SET ja.status='PAYMENT_DISPUTED'

        WHERE p.id=%s

    """, (
        payment_id,
    ))


    db.commit()

    cursor.close()
    db.close()


    return jsonify({
        "success": True,
        "message": "Payment dispute reported successfully.",
        "dispute_id": dispute_id
    }), 201



# ============================================================
# GET DUE WAGES FOR EMPLOYER
# ============================================================

@app.route('/get_due_wages', methods=['GET'])
def get_due_wages():

    employer_email = request.args.get(
        "email"
    )


    if not employer_email:

        return jsonify({
            "success": False,
            "message": "Employer email is required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # VERIFY EMPLOYER
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        employer_email,
    ))

    employer = cursor.fetchone()


    if not employer:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account not found."
        }), 404


    if employer["role"] != "Employer":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only employers can access due wages."
        }), 403


    if employer["status"] != "Active":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Employer account is not active."
        }), 403


    # --------------------------------------------------------
    # GET DUE WAGES
    # --------------------------------------------------------

    cursor.execute("""
        SELECT

            wr.id AS wage_id,

            wr.assignment_id,

            wr.work_session_id,

            wr.beneficiary_id,

            wr.employer_email,

            wr.work_date,

            wr.wage_earned,

            wr.wage_status,

            j.title AS job_title,

            b.full_name AS beneficiary_name,

            b.phone AS beneficiary_phone,

            b.location AS beneficiary_location

        FROM wage_records wr

        INNER JOIN job_assignments ja
            ON ja.id = wr.assignment_id

        INNER JOIN jobs j
            ON j.id = ja.job_id

        INNER JOIN beneficiaries b
            ON b.id = wr.beneficiary_id

        WHERE wr.employer_email=%s

        AND wr.wage_status='DUE'

        ORDER BY
            wr.work_date DESC,
            wr.id DESC

    """, (
        employer_email,
    ))


    wages = cursor.fetchall()


    cursor.close()
    db.close()


    # --------------------------------------------------------
    # FORMAT DATES
    # --------------------------------------------------------

    for wage in wages:

        if wage.get("work_date"):

            wage["work_date"] = (
                wage["work_date"]
                .strftime(
                    "%Y-%m-%d"
                )
            )


    return jsonify({
        "success": True,
        "wages": wages
    })



# ============================================================
# GET PAYMENT RECORDS
# ============================================================
@app.route('/get_payments', methods=['GET'])
def get_payments():
    email = request.args.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------------------------
    # VERIFY USER
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            email,
            name,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        email,
    ))

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404

    if user["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Account is not active."
        }), 403

    # --------------------------------------------------------
    # USE ROLE FROM DATABASE
    # --------------------------------------------------------
    role = user["role"]

    if role == "Beneficiary":
        cursor.execute("""
            SELECT
                p.id AS payment_id,

                p.assignment_id,
                p.amount,

                p.payment_method,
                p.payment_status,
                p.payment_date,

                p.employer_confirmation,
                p.beneficiary_confirmation,

                p.transaction_reference,

                wr.work_date,
                wr.wage_earned,

                j.title AS job_title,

                u.name AS employer_name

            FROM payments p

            INNER JOIN wage_records wr
                ON wr.id = p.wage_record_id

            INNER JOIN job_assignments ja
                ON ja.id = p.assignment_id

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = p.beneficiary_id

            INNER JOIN users bu
                ON bu.id = b.user_id

            LEFT JOIN users u
                ON u.email = p.employer_email

            WHERE bu.email=%s

            ORDER BY
                p.created_at DESC

        """, (
            email,
        ))

    elif role == "Admin":
        cursor.execute("""
            SELECT
                p.id AS payment_id,

                p.assignment_id,
                p.beneficiary_id,

                p.amount,

                p.payment_method,
                p.payment_status,
                p.payment_date,

                p.employer_confirmation,
                p.beneficiary_confirmation,

                p.transaction_reference,

                wr.work_date,
                wr.wage_earned,

                j.title AS job_title,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,

                u.name AS employer_name

            FROM payments p

            INNER JOIN wage_records wr
                ON wr.id = p.wage_record_id

            INNER JOIN job_assignments ja
                ON ja.id = p.assignment_id

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = p.beneficiary_id

            LEFT JOIN users u
                ON u.email = p.employer_email

            ORDER BY
                p.created_at DESC
        """)


    elif role in [
        "Volunteer",
        "NGO"
    ]:
        cursor.execute("""
            SELECT
                p.id AS payment_id,
                p.assignment_id,
                p.beneficiary_id,

                p.amount,
                p.payment_method,
                p.payment_status,
                p.payment_date,

                p.employer_confirmation,
                p.beneficiary_confirmation,

                p.transaction_reference,

                wr.work_date,
                wr.wage_earned,

                j.title AS job_title,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,

                u.name AS employer_name

            FROM payments p

            INNER JOIN wage_records wr
                ON wr.id = p.wage_record_id

            INNER JOIN job_assignments ja
                ON ja.id = p.assignment_id

            INNER JOIN job_applications app
                ON app.id = ja.application_id

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = p.beneficiary_id

            LEFT JOIN users u
                ON u.email = p.employer_email

            WHERE app.application_source='ASSISTED'
            AND app.submitted_by_email=%s

            ORDER BY
                p.created_at DESC

        """, (
            email,
        ))


    elif role == "Employer":
        cursor.execute("""
            SELECT
                p.id AS payment_id,

                p.assignment_id,
                p.beneficiary_id,

                p.amount,

                p.payment_method,
                p.payment_status,
                p.payment_date,

                p.employer_confirmation,
                p.beneficiary_confirmation,

                p.transaction_reference,

                wr.work_date,
                wr.wage_earned,

                j.title AS job_title,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone

            FROM payments p

            INNER JOIN wage_records wr
                ON wr.id = p.wage_record_id

            INNER JOIN job_assignments ja
                ON ja.id = p.assignment_id

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = p.beneficiary_id

            WHERE p.employer_email=%s

            ORDER BY
                p.created_at DESC

        """, (
            email,
        ))

    else:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Unauthorized role."
        }), 403

    payments = cursor.fetchall()

    cursor.close()
    db.close()

    for payment in payments:
        if payment.get("payment_date"):
            payment["payment_date"] = (
                payment["payment_date"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )

        if payment.get("work_date"):
            payment["work_date"] = (
                payment["work_date"]
                .strftime(
                    "%Y-%m-%d"
                )
            )

    return jsonify({
        "success": True,
        "payments": payments
    })



# ============================================================
# START LOCATION SHARING
# ============================================================
@app.route('/start_location_session', methods=['POST'])
def start_location_session():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    role = data.get("role")
    assignment_id = data.get("assignment_id")
    purpose = data.get("purpose")

    if not email or not role or not purpose or not assignment_id:
        return jsonify({
            "success": False,
            "message": "Email, role, purpose and assignment ID are required."
        }), 400


    allowed_roles = [
        "Beneficiary",
        "Volunteer",
        "NGO"
    ]

    if role not in allowed_roles:
        return jsonify({
            "success": False,
            "message": "This role cannot start a location session."
        }), 403


    allowed_purposes = [
        "GOING_TO_WORK",
        "ASSISTED_VISIT"
    ]

    if purpose not in allowed_purposes:
        return jsonify({
            "success": False,
            "message": "Invalid location-sharing purpose."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------------
    # VERIFY USER
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        email,
    ))

    user = cursor.fetchone()


    if not user:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404


    if user["role"] != role:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Role mismatch."
        }), 403


    if user["status"] != "Active":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Account is not active."
        }), 403


    # --------------------------------------------------------
    # ASSIGNMENT VALIDATION
    # --------------------------------------------------------
    if assignment_id:
        cursor.execute("""
            SELECT
                ja.id,
                ja.beneficiary_id,
                ja.status,

                b.user_id AS beneficiary_user_id,

                app.application_source,
                app.submitted_by_email

            FROM job_assignments ja

            INNER JOIN beneficiaries b
                ON b.id = ja.beneficiary_id

            INNER JOIN job_applications app
                ON app.id = ja.application_id

            WHERE ja.id=%s
        """, (
            assignment_id,
        ))

        assignment = cursor.fetchone()


    if not assignment:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Job assignment not found."
        }), 404


    # ----------------------------------------------------
    # BENEFICIARY CAN ONLY SHARE LOCATION
    # FOR THEIR OWN ASSIGNMENT
    # ----------------------------------------------------
    if role == "Beneficiary":
        if user["id"] != assignment["beneficiary_user_id"]:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "This assignment does not belong to you."
            }), 403


    if assignment["status"] in [
        "PAID",
        "PAYMENT_VERIFIED",
        "PAYMENT_DISPUTED"
    ]:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Location sharing is no longer available for this assignment."
        }), 409


    if role in [
        "Volunteer",
        "NGO"
    ]:

        if (
            assignment["application_source"] != "ASSISTED"
            or assignment["submitted_by_email"] != email
        ):
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "You are not authorized to share location for this assignment."
            }), 403


    # --------------------------------------------------------
    # STOP ANY EXISTING ACTIVE SESSION
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE location_sessions

        SET
            status='ENDED',
            ended_at=NOW()

        WHERE user_email=%s

        AND status='ACTIVE'
    """, (
        email,
    ))


    # --------------------------------------------------------
    # CREATE NEW SESSION
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO location_sessions
        (
            assignment_id,
            user_email,
            user_role,
            purpose,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            'ACTIVE'
        )
    """, (
        assignment_id,
        email,
        role,
        purpose
    ))


    session_id = cursor.lastrowid


    db.commit()

    cursor.close()
    db.close()


    return jsonify({
        "success": True,
        "message": "Location sharing started.",
        "session_id": session_id
    }), 201


# ============================================================
# UPDATE LOCATION
# ============================================================

@app.route('/update_location', methods=['POST'])
def update_location():

    data = request.get_json(silent=True) or {}

    session_id = data.get("session_id")
    email = data.get("email")

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    accuracy = data.get("accuracy")


    if (
        not session_id
        or not email
        or latitude is None
        or longitude is None
    ):

        return jsonify({
            "success": False,
            "message": "Location details are required."
        }), 400


    try:

        latitude = float(latitude)
        longitude = float(longitude)

        if accuracy is not None:
            accuracy = float(accuracy)

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "success": False,
            "message": "Invalid location values."
        }), 400


    if not (
        -90 <= latitude <= 90
    ):

        return jsonify({
            "success": False,
            "message": "Invalid latitude."
        }), 400


    if not (
        -180 <= longitude <= 180
    ):

        return jsonify({
            "success": False,
            "message": "Invalid longitude."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute("""
        SELECT
            id,
            status
        FROM location_sessions
        WHERE id=%s
        AND user_email=%s
    """, (
        session_id,
        email
    ))

    session = cursor.fetchone()


    if not session:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Location session not found."
        }), 404


    if session["status"] != "ACTIVE":

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Location session is no longer active."
        }), 409


    cursor.execute("""
        UPDATE location_sessions

        SET
            latitude=%s,
            longitude=%s,
            accuracy=%s,
            last_updated_at=NOW()

        WHERE id=%s
    """, (
        latitude,
        longitude,
        accuracy,
        session_id
    ))


    db.commit()

    cursor.close()
    db.close()


    return jsonify({
        "success": True,
        "message": "Location updated."
    })


# ============================================================
# STOP LOCATION SHARING
# ============================================================

@app.route('/stop_location_session', methods=['POST'])
def stop_location_session():

    data = request.get_json(silent=True) or {}

    session_id = data.get("session_id")
    email = data.get("email")


    if not session_id or not email:

        return jsonify({
            "success": False,
            "message": "Session ID and email are required."
        }), 400


    db = get_db()
    cursor = db.cursor()


    cursor.execute("""
        UPDATE location_sessions

        SET
            status='ENDED',
            ended_at=NOW()

        WHERE id=%s
        AND user_email=%s
        AND status='ACTIVE'
    """, (
        session_id,
        email
    ))


    if cursor.rowcount == 0:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Active location session not found."
        }), 404


    db.commit()

    cursor.close()
    db.close()


    return jsonify({
        "success": True,
        "message": "Location sharing stopped."
    })


# ============================================================
# ADMIN ACTIVE LOCATIONS
# ============================================================

@app.route('/admin/active_locations', methods=['GET'])
def admin_active_locations():

    email = request.args.get("email")


    if not email:

        return jsonify({
            "success": False,
            "message": "Admin email is required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        email,
    ))

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
            ls.id AS session_id,

            ls.assignment_id,

            ls.user_email,
            ls.user_role,

            ls.purpose,

            ls.latitude,
            ls.longitude,
            ls.accuracy,

            ls.started_at,
            ls.last_updated_at,

            b.full_name AS beneficiary_name,

            j.title AS job_title

        FROM location_sessions ls

        LEFT JOIN job_assignments ja
            ON ja.id = ls.assignment_id

        LEFT JOIN beneficiaries b
            ON b.id = ja.beneficiary_id

        LEFT JOIN jobs j
            ON j.id = ja.job_id

        WHERE ls.status='ACTIVE'

        AND (
            ls.last_updated_at >= DATE_SUB(
                NOW(),
                INTERVAL 5 MINUTE
            )
        )

        ORDER BY
            ls.last_updated_at DESC
    """)


    locations = cursor.fetchall()


    cursor.close()
    db.close()


    for location in locations:

        if location.get("started_at"):

            location["started_at"] = (
                location["started_at"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )


        if location.get("last_updated_at"):

            location["last_updated_at"] = (
                location["last_updated_at"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )


    return jsonify({
        "success": True,
        "locations": locations
    })


    
# ============================================================
# ADMIN EMPLOYMENT MONITORING
# ============================================================
@app.route('/admin/employment_overview', methods=['GET'])
def admin_employment_overview():
    admin_email = request.args.get("email")

    if not admin_email:

        return jsonify({
            "success": False,
            "message": "Admin email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # --------------------------------------------------------
    # VERIFY ADMIN
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        admin_email,
    ))

    admin = cursor.fetchone()

    if not admin:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin account not found."
        }), 404

    if admin["role"] != "Admin":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Only Admin can access employment monitoring."
        }), 403

    if admin["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin account is not active."
        }), 403

    # ========================================================
    # OVERVIEW COUNTS
    # ========================================================
    cursor.execute("""
        SELECT
            COUNT(*) AS total_assignments,

            SUM(
                CASE
                    WHEN status='IN_PROGRESS'
                    THEN 1 ELSE 0
                END
            ) AS in_progress,

            SUM(
                CASE
                    WHEN status='WORK_COMPLETED'
                    THEN 1 ELSE 0
                END
            ) AS work_completed,

            SUM(
                CASE
                    WHEN status='PAYMENT_DUE'
                    THEN 1 ELSE 0
                END
            ) AS payment_due,

            SUM(
                CASE
                    WHEN status='PAID'
                    THEN 1 ELSE 0
                END
            ) AS paid,

            SUM(
                CASE
                    WHEN status='PAYMENT_VERIFIED'
                    THEN 1 ELSE 0
                END
            ) AS payment_verified

        FROM job_assignments
    """)

    overview = cursor.fetchone()

    # ========================================================
    # EMPLOYMENT RECORDS
    # ========================================================
    cursor.execute("""
        SELECT

            ja.id AS assignment_id,

            ja.status AS assignment_status,

            ja.work_date,
            ja.work_location,
            ja.meeting_point,

            ja.agreed_wage,
            ja.wage_type,

            ja.payment_commitment,

            ja.accepted_at,

            ja.employer_email,

            j.title AS job_title,

            b.full_name AS beneficiary_name,
            b.phone AS beneficiary_phone,
            b.location AS beneficiary_location,

            employer.name AS employer_name,

            ws.id AS work_session_id,
            ws.start_time,
            ws.end_time,
            ws.hours_worked,
            ws.attendance_status,
            ws.work_status,

            wr.id AS wage_id,
            wr.wage_earned,
            wr.wage_status,

            p.id AS payment_id,
            p.amount AS payment_amount,
            p.payment_method,
            p.payment_status,
            p.payment_date,
            p.transaction_reference,
            p.employer_confirmation,
            p.beneficiary_confirmation

        FROM job_assignments ja

        INNER JOIN jobs j
            ON j.id = ja.job_id

        INNER JOIN beneficiaries b
            ON b.id = ja.beneficiary_id

        LEFT JOIN users employer
            ON employer.email = ja.employer_email

        LEFT JOIN work_sessions ws
            ON ws.assignment_id = ja.id

        LEFT JOIN wage_records wr
            ON wr.work_session_id = ws.id

        LEFT JOIN payments p
            ON p.wage_record_id = wr.id

        ORDER BY
            ja.work_date DESC,
            ja.accepted_at DESC

    """)

    records = cursor.fetchall()

    cursor.close()
    db.close()

    # ========================================================
    # FORMAT DATETIME / DATE VALUES
    # ========================================================
    for record in records:
        if record.get("work_date"):
            record["work_date"] = (
                record["work_date"]
                .strftime("%Y-%m-%d")
            )

        if record.get("accepted_at"):
            record["accepted_at"] = (
                record["accepted_at"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )

        if record.get("start_time"):
            record["start_time"] = (
                record["start_time"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )

        if record.get("end_time"):
            record["end_time"] = (
                record["end_time"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )

        if record.get("payment_date"):
            record["payment_date"] = (
                record["payment_date"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )

    return jsonify({
        "success": True,

        "overview":
            overview,

        "records":
            records
    })


# ============================================================
# GET WORK SESSIONS
# ============================================================
@app.route('/get_work_sessions', methods=['GET'])
def get_work_sessions():

    email = request.args.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400


    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            email,
            role,
            status
        FROM users
        WHERE email=%s
    """, (
        email,
    ))

    user = cursor.fetchone()


    if not user:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404

    if user["status"] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Account is not active."
        }), 403

    role = user["role"]


    if role == "Employer":
        cursor.execute("""
            SELECT
                ws.id AS session_id,

                ws.assignment_id,
                ws.beneficiary_id,

                ws.work_date,
                ws.start_time,
                ws.end_time,

                ws.hours_worked,

                ws.attendance_status,
                ws.work_status,

                ws.employer_notes,

                ws.beneficiary_confirmation,

                ja.employer_email,

                j.title AS job_title,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone

            FROM work_sessions ws

            INNER JOIN job_assignments ja
                ON ja.id = ws.assignment_id

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = ws.beneficiary_id

            WHERE ws.employer_email=%s

            ORDER BY
                ws.work_date DESC,
                ws.id DESC

        """, (
            email,
        ))


    elif role == "Beneficiary":

        cursor.execute("""
            SELECT

                ws.id AS session_id,

                ws.assignment_id,
                ws.beneficiary_id,

                ws.work_date,
                ws.start_time,
                ws.end_time,

                ws.hours_worked,

                ws.attendance_status,
                ws.work_status,

                ws.employer_notes,

                ws.beneficiary_confirmation,

                j.title AS job_title,

                u.name AS employer_name

            FROM work_sessions ws

            INNER JOIN job_assignments ja
                ON ja.id = ws.assignment_id

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = ws.beneficiary_id

            INNER JOIN users bu
                ON bu.id = b.user_id

            LEFT JOIN users u
                ON u.email = ja.employer_email

            WHERE bu.email=%s

            ORDER BY
                ws.work_date DESC,
                ws.id DESC

        """, (
            email,
        ))


    elif role == "Admin":
        cursor.execute("""
            SELECT

                ws.id AS session_id,

                ws.assignment_id,
                ws.beneficiary_id,

                ws.work_date,
                ws.start_time,
                ws.end_time,

                ws.hours_worked,

                ws.attendance_status,
                ws.work_status,

                ws.employer_notes,

                ws.beneficiary_confirmation,

                ja.employer_email,

                j.title AS job_title,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,

                u.name AS employer_name

            FROM work_sessions ws

            INNER JOIN job_assignments ja
                ON ja.id = ws.assignment_id

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = ws.beneficiary_id

            LEFT JOIN users u
                ON u.email = ja.employer_email

            ORDER BY
                ws.work_date DESC,
                ws.id DESC

        """)



    elif role in [
        "Volunteer",
        "NGO"
    ]:

        cursor.execute("""
            SELECT
                ws.id AS session_id,
                ws.assignment_id,
                ws.beneficiary_id,

                ws.work_date,
                ws.start_time,
                ws.end_time,

                ws.hours_worked,

                ws.attendance_status,
                ws.work_status,

                ws.employer_notes,
                ws.beneficiary_confirmation,

                ja.employer_email,

                j.title AS job_title,

                b.full_name AS beneficiary_name,
                b.phone AS beneficiary_phone,
                b.location AS beneficiary_location,

                u.name AS employer_name

            FROM work_sessions ws

            INNER JOIN job_assignments ja
                ON ja.id = ws.assignment_id

            INNER JOIN job_applications app
                ON app.id = ja.application_id

            INNER JOIN jobs j
                ON j.id = ja.job_id

            INNER JOIN beneficiaries b
                ON b.id = ws.beneficiary_id

            LEFT JOIN users u
                ON u.email = ja.employer_email

            WHERE app.application_source='ASSISTED'
            AND app.submitted_by_email=%s

            ORDER BY
                ws.work_date DESC,
                ws.id DESC

        """, (
            email,
        ))


    else:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Unauthorized role."
        }), 403


    sessions = cursor.fetchall()


    cursor.close()
    db.close()


    for session in sessions:

        if session.get("work_date"):

            session["work_date"] = (
                session["work_date"]
                .strftime("%Y-%m-%d")
            )


        if session.get("start_time"):

            session["start_time"] = (
                session["start_time"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )


        if session.get("end_time"):

            session["end_time"] = (
                session["end_time"]
                .strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            )


    return jsonify({
        "success": True,
        "sessions": sessions
    })



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

    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (
        email,
    ))

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404

    if user[1] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Account is not active."
        }), 403

    role = user[0]

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

    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (
        email,
    ))

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "User account not found."
        }), 404

    if user[1] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Account is not active."
        }), 403

    role = user[0]

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
    admin_email = request.args.get("email")

    if not admin_email:
        return jsonify({
            "success": False,
            "message": "Admin email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (
        admin_email,
    ))

    admin = cursor.fetchone()

    if not admin:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin account not found."
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
        SELECT role, COUNT(*) AS total
        FROM users
        GROUP BY role
    """)

    rows = cursor.fetchall()

    counts = {
        "Total": 0,
        "Admin": 0,
        "Volunteer": 0,
        "NGO": 0,
        "Donor": 0,
        "Employer": 0
    }

    for row in rows:
        role = row["role"]
        total = row["total"]

        counts[role] = total

        counts["Total"] += total

    cursor.close()
    db.close()

    return jsonify(counts)


@app.route("/api/admin/users/<role>", methods=["GET"])
def admin_get_users(role):
    admin_email = request.args.get("email")

    if not admin_email:
        return jsonify({
            "success": False,
            "message": "Admin email is required."
        }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (
        admin_email,
    ))

    admin = cursor.fetchone()

    if not admin:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin account not found."
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
    admin_email = request.args.get("email")

    if not admin_email:
        return jsonify({
            "success": False,
            "message": "Admin email is required."
        }), 400

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT role, status
        FROM users
        WHERE email=%s
    """, (
        admin_email,
    ))

    admin = cursor.fetchone()

    if not admin:
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin account not found."
        }), 404

    if admin[0] != "Admin":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    if admin[1] != "Active":
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin account is not active."
        }), 403

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
    admin_email = request.args.get("email")

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