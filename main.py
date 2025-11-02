import os
from flask import Flask, render_template, redirect, request, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

curr_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///household_services.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "tawp_sekret"

app.config['UPLOAD_PATH'] = os.path.join(curr_dir, 'static', 'pdfs')

db = SQLAlchemy()

db.init_app(app)


# ORM -> Object Relational Mapping

class Customer(db.Model):
    __tablename__= "customer"
    cust_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_name = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80))
    date_created = db.Column(db.String(80), default=datetime.now().date().strftime("%d/%m/%Y"))
    address = db.Column(db.String(80), nullable=False)
    pin_code = db.Column(db.Integer, nullable=False)
    contact = db.Column(db.Integer, nullable=False)

    # One-to-Many relationship between customer and service requests
    service_request = db.relationship("ServiceRequest", backref="customer_requested", lazy=True, cascade="all, delete-orphan")

class ServiceProfessional(db.Model):
    __tablename__="serviceprofessional"
    pro_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_name = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80))
    date_created = db.Column(db.String(80), default = datetime.now().date().strftime("%d/%m/%Y"))
    description = db.Column(db.String(150), nullable=False)
    service_type = db.Column(db.String(80), db.ForeignKey("services.name"), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    resume = db.Column(db.String(80))
    contact = db.Column(db.Integer, nullable=False)
    approval_status = db.Column(db.String(80), default="Pending")
    avg_rating = db.Column(db.Integer, default=0)
    pincode = db.Column(db.String(6), nullable=False)

    # One-to-Many relationship between professional and service requests
    all_requests = db.relationship("ServiceRequest", backref="professional_requested", lazy=True, cascade="all, delete-orphan")

class Services(db.Model):
    __tablename__="services"
    serv_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    time_required = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(150), nullable=False)

    # One-to-Many relationship between service and service requests
    service_requests = db.relationship("ServiceRequest", backref="service_offered", lazy=True, cascade="all, delete-orphan")

    # One-to-Many relationship between service and service professionals
    professionals = db.relationship("ServiceProfessional", backref="service_employed_under", lazy=True, cascade="all, delete-orphan")

class ServiceRequest(db.Model):
    __tablename__="servicerequest"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.serv_id"))
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.cust_id"))
    professional_id = db.Column(db.Integer, db.ForeignKey("serviceprofessional.pro_id"))
    date_of_request = db.Column(db.String(80), default = datetime.now().date().strftime("%d/%m/%Y"))
    date_of_completion = db.Column(db.String(80))
    service_status = db.Column(db.String(80), default="Requested")
    ratings = db.Column(db.Integer, default=0)
    remarks = db.Column(db.String(150))

with app.app_context():
    db.create_all()

# Initialization of session variables
def init_session():
    if not session.get("user_id"):
        session["user_id"] = None
    if not session.get("user_username"):
        session["user_username"] = None

@app.before_request
def before_request():
    init_session()

# Routes

## Home
@app.route("/")
def home():
    return render_template("home.html")

## Login Pages for Customers and Service Professionals

@app.route("/login/employee", methods=["GET", "POST"])
def employee_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["user_id"] = "admin"
            session["user_username"] = "admin"
            return redirect(url_for("admin_dashboard"))
        else:
            user_name = request.form["username"]
            password = request.form["password"]
            employee = ServiceProfessional.query.filter_by(user_name=user_name).first()
            if employee == None:
                flash("Username does not exist","error")
                return render_template("employee_login.html")
            else:
                if check_password_hash(employee.password, password):
                    if employee.approval_status == "Approved":
                        session["user_id"] = employee.pro_id
                        session["user_username"] = employee.user_name
                        return redirect(url_for("professional_dashboard"))
                    elif employee.approval_status == "Blocked":
                        flash("Your account is blocked, please contact administrator","error")
                        return render_template("employee_login.html")
                    else:
                        flash("Your account is pending for approval","error")
                        return render_template("employee_login.html")
                else:
                    flash("Incorrect password","error")
                    return render_template("employee_login.html")
                
    return render_template("employee_login.html")


@app.route(("/login/customer"), methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["user_id"] = "admin"
            session["user_username"] = "admin"
            return redirect(url_for("admin_dashboard"))
        else:
            user_name = request.form["username"]
            password = request.form["password"]
            customer = Customer.query.filter_by(user_name=user_name).first()
            if customer == None:
                flash("Username does not exist","error")
                return render_template("customer_login.html")
            else:
                if check_password_hash(customer.password, password):
                    session["user_id"] = customer.cust_id
                    session["user_username"] = customer.user_name
                    return redirect(url_for("customer_dashboard"))
                else:
                    flash("Incorrect password","error")
                    return render_template("customer_login.html")
                
    return render_template("customer_login.html")

ALLOWED_EXTENSIONS = ['pdf']

def allowed_extensions(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

## Register Pages for Customers and Service Professionals

@app.route("/register/employee", methods=["GET", "POST"])
def employee_register():
    services = Services.query.all()
    if request.method == "POST":
        user_name = request.form["username"]
        password = generate_password_hash(request.form["password"])
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        experience = request.form["work_exp"]
        service_name = request.form["service"]
        service_description = request.form["service_description"]
        resume = request.files["resume"]
        contact = request.form["contact"]
        pincode = request.form["pincode"]

        if ServiceProfessional.query.filter_by(user_name=user_name).first() != None:
            flash("Username already exists","error")
            return render_template("employee_register.html", services=services)
        else:
            if resume != "" and allowed_extensions(resume.filename):
                resume.save(os.path.join(app.config['UPLOAD_PATH'], user_name+"_resume.pdf"))
            else:
                flash("Only PDF files are allowed","error")
                return render_template("employee_register.html", services=services)
            new_employee = ServiceProfessional(user_name=user_name, password=password, first_name=first_name, last_name=last_name, service_type=service_name, description=service_description, experience=experience,resume=user_name+"_resume.pdf",contact=contact,pincode=pincode)
            db.session.add(new_employee)
            db.session.commit()
            flash("Account created successfully","success")
            return render_template("employee_login.html")
    return render_template("employee_register.html", services=services)


@app.route("/register/customer", methods=["GET", "POST"])
def customer_register():
    if request.method == "POST":
        user_name = request.form["username"]
        password = generate_password_hash(request.form["password"])
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        address = request.form["address"]
        pincode = request.form["pincode"]
        contact = request.form["contact"]

        if Customer.query.filter_by(user_name=user_name).first() != None:
            flash("Username already exists","error")
            return render_template("customer_register.html")
        else:
            new_customer = Customer(user_name=user_name, password=password, first_name=first_name, last_name=last_name, address=address, pin_code=pincode,contact=contact)  
            db.session.add(new_customer)
            db.session.commit()
            flash("Account created successfully","success")
            return render_template("customer_login.html")
    return render_template("customer_register.html")

## Dashboard for Admin

@app.route("/admin/dashboard")
def admin_dashboard():
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        
        # Handled Services Here
        services = Services.query.all()
        service_list = []
        sub_list = []
        count = 0
        for s in range(len(services)):
            if count != 5:
                sub_list.append(services[s])
                count += 1
            elif count == 5:
                service_list.append(sub_list)
                sub_list = []
                count = 0
                sub_list.append(services[s])
                count += 1
            if s == len(services) - 1 and count != 0:
                service_list.append(sub_list)
        
        # Handled Service Professionals Here according to ratings
        service_professionals = ServiceProfessional.query.order_by(ServiceProfessional.avg_rating.desc()).all()

        # Handled Service Requests Here
        all_requests = ServiceRequest.query.all()
        service_requests = []
        for req in all_requests:
            service_requests.append((req, ServiceProfessional.query.filter_by(pro_id=req.professional_id).first()))

        return render_template("admin_dashboard_home.html", service_list=service_list, service_professionals=service_professionals, service_requests = service_requests)
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

# CRUD for Services

# Creating a Service
@app.route("/admin/create/service", methods=["GET", "POST"])
def create_service():
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        if request.method == "POST":
            service_name = request.form["service_name"]
            service_rate = request.form["service_rate"]
            time_required = request.form["time_required"]
            service_description = request.form["service_description"]

            if Services.query.filter_by(name=service_name).first() != None:
                flash("Service already exists","error")
                return render_template("create_service.html")
            else:
                new_service = Services(name=service_name, price=service_rate, time_required=time_required, description=service_description)
                db.session.add(new_service)
                db.session.commit()
                flash("Service created successfully","success")
                return redirect(url_for("admin_dashboard"))
        return render_template("create_service.html")
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

# Updating a Service
@app.route("/admin/edit/service/<int:service_id>", methods=["GET", "POST"])
def edit_service(service_id):
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        service = Services.query.filter_by(serv_id=service_id).first()
        if request.method == "POST":
            service_name = request.form["service_name"]
            service_rate = request.form["service_rate"]
            time_required = request.form["time_required"]
            service_description = request.form["service_description"]
            if service_name != service.name:
                if Services.query.filter_by(name=service_name).first() != None:
                    flash("Service already exists","error")
                    return render_template("edit_service.html", service = service)
                else:
                    service.name = service_name
                service.price = service_rate
                service.time_required = time_required
                service.description = service_description
            else:
                service.price = service_rate
                service.time_required = time_required
                service.description = service_description
            db.session.commit()
            flash("Service updated successfully","success")
            return redirect(url_for("admin_dashboard"))
        return render_template("edit_service.html", service = service)

# Deleting a Service
@app.route("/admin/delete/service/<int:service_id>")
def delete_service(service_id):
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        service = Services.query.filter_by(serv_id=service_id).first()
        db.session.delete(service)
        db.session.commit()
        flash("Service deleted successfully","success")
        return redirect(url_for("admin_dashboard"))
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

# Approval of Professionals

@app.route("/admin/approve/professional/<int:professional_id>")
def approve_professional(professional_id):
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        professional = ServiceProfessional.query.filter_by(pro_id=professional_id).first()
        professional.approval_status = "Approved"
        service = Services.query.filter_by(name=professional.service_type).first()
        service.professionals.append(professional)
        db.session.commit()
        flash("Professional approved successfully","success")
        return redirect(url_for("admin_dashboard"))
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

# Rejection and Removal of Professionals

@app.route("/admin/reject/professional/<int:professional_id>")
def reject_professional(professional_id):
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        professional = ServiceProfessional.query.filter_by(pro_id=professional_id).first()
        db.session.delete(professional)
        db.session.commit()
        flash("Professional rejected and deleted successfully","success")
        return redirect(url_for("admin_dashboard"))
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

# Blocking Professionals

@app.route("/admin/block/professional/<int:professional_id>")
def block_professional(professional_id):
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        professional = ServiceProfessional.query.filter_by(pro_id=professional_id).first()
        professional.approval_status="Blocked"
        db.session.commit()
        flash("Professional blocked successfully","success")
        return redirect(url_for("admin_dashboard"))
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

# Unblocking Professionals

@app.route("/admin/unblock/professional/<int:professional_id>")
def unblock_professional(professional_id):
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        professional = ServiceProfessional.query.filter_by(pro_id=professional_id).first()
        professional.approval_status="Approved"
        db.session.commit()
        flash("Professional unblocked successfully","success")
        return redirect(url_for("admin_dashboard"))
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

# Admin Dashboard Search

@app.route("/admin/dashboard/search", methods=["GET", "POST"])
def admin_dashboard_search():
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        if request.method == "POST":
            filter = request.form["filter"]
            search_input = request.form["search_input"]
            if filter == "service_name":
                services = Services.query.filter(Services.name.ilike("%"+search_input+"%")).all()
                all_req = []
                for serv in services:
                    all_req.extend(serv.service_requests)
                service_requests = []
                for req in all_req:
                    service_requests.append((req,Customer.query.filter_by(cust_id=req.customer_id).first(), Services.query.filter_by(serv_id=req.service_id).first().name, ServiceProfessional.query.filter_by(pro_id=req.professional_id).first()))
                return render_template("admin_dashboard_search.html", service_requests=service_requests, last_input=search_input, filter_search=filter)
            elif filter == "date_of_req":
                requests = ServiceRequest.query.filter(ServiceRequest.date_of_request.ilike("%"+search_input+"%")).all()
                service_requests = []
                for req in requests:
                    service_requests.append((req,Customer.query.filter_by(cust_id=req.customer_id).first(), Services.query.filter_by(serv_id=req.service_id).first().name, ServiceProfessional.query.filter_by(pro_id=req.professional_id).first()))
                return render_template("admin_dashboard_search.html", service_requests=service_requests, last_input=search_input, filter_search=filter)
            elif filter == "professional_name":
                professional_first_name = ServiceProfessional.query.filter(ServiceProfessional.first_name.ilike("%"+search_input+"%")).all()
                professional_last_name = ServiceProfessional.query.filter(ServiceProfessional.last_name.ilike("%"+search_input+"%")).all()
                professional_user_name = ServiceProfessional.query.filter(ServiceProfessional.user_name.ilike("%"+search_input+"%")).all()
                pros = list(set(professional_first_name + professional_last_name + professional_user_name))
                all_req = []
                for pro in pros:
                    all_req.extend(pro.all_requests)
                service_requests = []
                for req in all_req:
                    service_requests.append((req,Customer.query.filter_by(cust_id=req.customer_id).first(), Services.query.filter_by(serv_id=req.service_id).first().name, ServiceProfessional.query.filter_by(pro_id=req.professional_id).first()))
                return render_template("admin_dashboard_search.html", service_requests=service_requests, last_input=search_input, filter_search=filter)
            elif filter == "customer_name":
                customer_first_name = Customer.query.filter(Customer.first_name.ilike("%"+search_input+"%")).all()
                customer_last_name = Customer.query.filter(Customer.last_name.ilike("%"+search_input+"%")).all()
                customer_user_name = Customer.query.filter(Customer.user_name.ilike("%"+search_input+"%")).all()
                customers = list(set(customer_first_name + customer_last_name + customer_user_name))
                all_req = []
                for customer in customers:
                    all_req.extend(customer.service_request)
                service_requests = []
                for req in all_req:
                    service_requests.append((req, Customer.query.filter_by(cust_id=req.customer_id).first(), Services.query.filter_by(serv_id=req.service_id).first().name, ServiceProfessional.query.filter_by(pro_id=req.professional_id).first()))
                return render_template("admin_dashboard_search.html", service_requests=service_requests, last_input=search_input, filter_search=filter)
        all_req = ServiceRequest.query.all()
        service_requests = []
        for req in all_req:
            service_requests.append((req, Customer.query.filter_by(cust_id=req.customer_id).first(), Services.query.filter_by(serv_id=req.service_id).first().name, ServiceProfessional.query.filter_by(pro_id=req.professional_id).first()))
        return render_template("admin_dashboard_search.html", service_requests=service_requests)
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

# Summary of Admin Dashboard

@app.route("/admin/dashboard/summary")
def admin_dashboard_summary():
    if session['user_id'] == "admin" and session['user_username'] == "admin":
        rejected_req = len(ServiceRequest.query.filter_by(service_status="Rejected").all())
        accepted_req = len(ServiceRequest.query.filter_by(service_status="Accepted").all())
        pending_req = len(ServiceRequest.query.filter_by(service_status="Requested").all())
        closed_req = len(ServiceRequest.query.filter_by(service_status="Closed").all())
        x = ['Rejected', 'Accepted', 'Pending', 'Closed']
        y = [rejected_req, accepted_req, pending_req, closed_req]
        return render_template("admin_dashboard_summary.html", x=x, y=y)
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

## Professional Dashboard

@app.route("/professional/dashboard")
def professional_dashboard():
    if ServiceProfessional.query.filter_by(pro_id=session['user_id'], approval_status = "Approved").first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        professional = ServiceProfessional.query.filter_by(pro_id=session['user_id']).first()
        public_requests = ServiceRequest.query.filter_by(professional_id=None, service_id=Services.query.filter_by(name=professional.service_type).first().serv_id, service_status="Requested").all() 
        private_requests = ServiceRequest.query.filter_by(professional_id=session['user_id'], service_status="Requested").all()
        accepted_requests = ServiceRequest.query.filter_by(professional_id=session['user_id'], service_status="Accepted").all()
        closed_requests = ServiceRequest.query.filter_by(professional_id=session['user_id'], service_status="Closed").all()

        mod_pub_req = []
        mod_pri_req = []
        mod_acp_req = []
        mod_clo_req = []

        for req in public_requests:
            mod_pub_req.append((req, Customer.query.filter_by(cust_id=req.customer_id).first()))
        for req in private_requests:
            mod_pri_req.append((req, Customer.query.filter_by(cust_id=req.customer_id).first()))
        for req in accepted_requests:
            mod_acp_req.append((req, Customer.query.filter_by(cust_id=req.customer_id).first()))
        for req in closed_requests:
            mod_clo_req.append((req, Customer.query.filter_by(cust_id=req.customer_id).first()))
        
        return render_template("professional_dashboard_home.html", public_requests=mod_pub_req, private_requests=mod_pri_req, accepted_requests=mod_acp_req, closed_requests=mod_clo_req)

# Accepting Requests

@app.route("/professional/accept/request/<int:request_id>")
def accept_request(request_id):
    if ServiceProfessional.query.filter_by(pro_id = session["user_id"], approval_status = "Approved").first() != None:
        pro = ServiceProfessional.query.filter_by(pro_id=session["user_id"]).first()
        req = ServiceRequest.query.filter_by(id=request_id).first()
        req.service_status = "Accepted"
        if req.professional_id == None:
            req.professional_id = session["user_id"]
        pro.all_requests.append(req)
        db.session.commit()
        flash("Request accepted successfully","success")
        return redirect(url_for("professional_dashboard"))
    else:
        flash("Unauthorised Access","error")    
        return redirect(url_for("home"))

# Rejecting Requests

@app.route("/professional/reject/request/<int:request_id>")
def reject_request(request_id):
    if ServiceProfessional.query.filter_by(pro_id = session["user_id"], approval_status = "Approved").first() != None:
        pro = ServiceProfessional.query.filter_by(pro_id=session["user_id"]).first()
        req = ServiceRequest.query.filter_by(id=request_id).first()
        req.service_status = "Rejected"
        pro.all_requests.append(req)
        db.session.commit()
        flash("Request rejected successfully","success")
        return redirect(url_for("professional_dashboard"))
    else:
        flash("Unauthorised Access","error")    
        return redirect(url_for("home"))

# Professional Dashboard Summary

@app.route("/professional/dashboard/summary")
def professional_dashboard_summary():
    if ServiceProfessional.query.filter_by(pro_id=session['user_id'], approval_status = "Approved").first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        x = ['Rejected', 'Accepted', 'Received', 'Closed']
        rej_req = len(ServiceRequest.query.filter_by(professional_id=session['user_id'], service_status="Rejected").all())
        rec_req = len(ServiceRequest.query.filter_by(professional_id=session['user_id'], service_status="Requested").all())
        acc_req = len(ServiceRequest.query.filter_by(professional_id=session['user_id'], service_status="Accepted").all())
        clo_req = len(ServiceRequest.query.filter_by(professional_id=session['user_id'], service_status="Closed").all())
        y = [rej_req, acc_req, rec_req, clo_req]
        return render_template("professional_dashboard_summary.html", x=x, y=y)

## Customer Dashboard

@app.route("/customer/dashboard")
def customer_dashboard():
    if Customer.query.filter_by(cust_id=session['user_id']).first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        # Handled Servcies here
        services = Services.query.all()
        service_list = []
        sub_list = []
        count = 0
        for s in range(len(services)):
            if count != 5:
                sub_list.append(services[s])
                count += 1
            elif count == 5:
                service_list.append(sub_list)
                sub_list = []
                count = 0
                sub_list.append(services[s])
                count += 1
            if s == len(services) - 1 and count != 0:
                service_list.append(sub_list)
        
        # Handled Requests here
        requests = ServiceRequest.query.filter_by(customer_id=session['user_id']).all()
        mod_req_list = []

        for req in requests:
            service = Services.query.filter_by(serv_id=req.service_id).first()
            professional = ServiceProfessional.query.filter_by(pro_id=req.professional_id).first()
            if professional == None:
                mod_req_list.append(("No Professional Accepted Yet", service.name, req.service_status, "No Contact", req.id, req.date_of_request))
            else:
                mod_req_list.append((professional.user_name, professional.service_type, req.service_status, professional.contact, req.id, req.date_of_request))
        
        return render_template("customer_dashboard_home.html", service_list=service_list, mod_req_list=mod_req_list)

# Viewing a service with its professionals

@app.route("/customer/view/service/<int:service_id>")
def customer_view_service(service_id):
    if Customer.query.filter_by(cust_id=session['user_id']).first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        service = Services.query.filter_by(serv_id=service_id).first()
        pros = ServiceProfessional.query.filter_by(service_type=service.name, approval_status="Approved").order_by(ServiceProfessional.avg_rating.desc()).all()
        
        return render_template("customer_dashboard_view_service.html", service=service, pros=pros)

# Creating a public request

@app.route("/customer/create/request/<int:service_id>")
def create_public_request(service_id):
    if Customer.query.filter_by(cust_id=session['user_id']).first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        service = Services.query.filter_by(serv_id=service_id).first()
        if ServiceRequest.query.filter_by(professional_id=None,service_id=service_id, customer_id=session['user_id'], service_status="Requested").first() != None:
            flash("You already have a request open for this service","error")
            return redirect(url_for("customer_dashboard"))
        else:
            new_request = ServiceRequest(service_id=service_id, customer_id=session['user_id'])
            service.service_requests.append(new_request)
            customer = Customer.query.filter_by(cust_id=session['user_id']).first()
            customer.service_request.append(new_request)
            db.session.add(new_request)
            db.session.commit()
            flash("Request created successfully","success")
            return redirect(url_for("customer_dashboard"))

# Creating a private request

@app.route("/customer/create/request/<int:service_id>/<int:professional_id>")
def create_private_request(service_id, professional_id):
    if Customer.query.filter_by(cust_id=session['user_id']).first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        if ServiceRequest.query.filter_by(service_id=service_id, customer_id=session['user_id'],professional_id=professional_id , service_status="Requested").first() != None:
            flash("You already have a request open for this service","error")
            return redirect(url_for("customer_dashboard"))
        elif ServiceRequest.query.filter_by(service_id=service_id, customer_id=session['user_id'],professional_id=professional_id , service_status="Accepted").first() != None:
            flash("You already have a request open for this service","error")
            return redirect(url_for("customer_dashboard"))
        else:
            service = Services.query.filter_by(serv_id=service_id).first()
            new_request = ServiceRequest(service_id=service_id, customer_id=session['user_id'], professional_id=professional_id)
            service.service_requests.append(new_request)
            customer = Customer.query.filter_by(cust_id=session['user_id']).first()
            customer.service_request.append(new_request)
            db.session.add(new_request)
            db.session.commit()
            flash("Request created successfully","success")
            return redirect(url_for("customer_dashboard"))

# Editing a request

@app.route("/customer/edit/request/<int:request_id>", methods=["GET", "POST"])
def edit_request(request_id):
    if Customer.query.filter_by(cust_id=session['user_id']).first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        req = ServiceRequest.query.filter_by(id=request_id).first()
        dor = datetime.strptime(req.date_of_request, "%d/%m/%Y").date().strftime("%Y-%m-%d")
        if request.method == "POST":
            if req.service_status == "Closed":
                req.remarks = request.form["remark"]
                db.session.commit()
                flash("Request edited successfully","success")
                return redirect(url_for("customer_dashboard"))
            else:
                new_date_of_req = datetime.strptime(request.form["date_of_req"], "%Y-%m-%d").date().strftime("%d/%m/%Y")
                req.date_of_request = new_date_of_req 
                db.session.commit()
                flash("Request edited successfully","success")
                return redirect(url_for("customer_dashboard"))
        
        return render_template("edit_request.html", req=req, dor=dor)

# Delete Request

@app.route("/customer/delete/request/<int:request_id>")
def delete_request(request_id):
    if Customer.query.filter_by(cust_id=session['user_id']).first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        req = ServiceRequest.query.filter_by(id=request_id).first()
        db.session.delete(req)
        db.session.commit()
        flash("Request deleted successfully","success")
        return redirect(url_for("customer_dashboard"))

# Closing Requests

@app.route("/customer/close/request/<int:request_id>", methods=["GET", "POST"])
def close_request(request_id):
    if Customer.query.filter_by(cust_id=session['user_id']).first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        current_date = datetime.now().date().strftime("%d/%m/%Y")
        req = ServiceRequest.query.filter_by(id=request_id).first()
        pro = ServiceProfessional.query.filter_by(pro_id=req.professional_id).first()
        if request.method == "POST":
            rating = request.form["rating"]
            remarks = request.form["remarks"]
            req.ratings = rating
            req.remarks = remarks
            req.date_of_completion = current_date
            req.service_status = "Closed"
            db.session.commit()

            # Updating average rating of professional
            sum_ratings = 0
            count_closed_req = 0
            for req in pro.all_requests:
                if req.service_status == "Closed":
                    sum_ratings += req.ratings
                    count_closed_req += 1
            if len(pro.all_requests) != 0:
                pro.avg_rating = sum_ratings / count_closed_req
            db.session.commit()

            flash("Request closed successfully","success")
            return redirect(url_for("customer_dashboard"))
        return render_template("close_request.html", pro=pro, req=req, current_date=current_date)
    
# Customer Dashboard Search

@app.route("/customer/dashboard/search", methods=["GET", "POST"])
def customer_dashboard_search():
    if Customer.query.filter_by(cust_id=session['user_id']).first() != None:
        if request.method == "POST":
            filter = request.form["filter"]
            search_input = request.form["search_input"]
            if filter == "service_name":
                services = Services.query.filter(Services.name.ilike("%"+search_input+"%"),ServiceProfessional.approval_status=="Approved").all()
                all_pros = []
                for serv in services:
                    all_pros.extend(serv.professionals)
                service_professionals = []
                for pro in all_pros:
                    service_professionals.append((pro, Services.query.filter_by(name=pro.service_type).first()))
                return render_template("customer_dashboard_search.html", service_professionals=service_professionals, last_input=search_input, filter_search=filter)
            elif filter == "pro_pincode":
                pros = ServiceProfessional.query.filter(ServiceProfessional.pincode.ilike("%"+search_input+"%"),ServiceProfessional.approval_status=="Approved").all()
                service_professionals = []
                for pro in pros:
                    service_professionals.append((pro, Services.query.filter_by(name=pro.service_type).first()))
                return render_template("customer_dashboard_search.html", service_professionals=service_professionals, last_input=search_input, filter_search=filter)
            elif filter == "professional_name":
                professional_user_name = ServiceProfessional.query.filter(ServiceProfessional.user_name.ilike("%"+search_input+"%"),ServiceProfessional.approval_status=="Approved").all()
                pros = professional_user_name
                service_professionals = []
                for pro in pros:
                    service_professionals.append((pro, Services.query.filter_by(name=pro.service_type).first()))
                return render_template("customer_dashboard_search.html", service_professionals=service_professionals, last_input=search_input, filter_search=filter)
            elif filter == "avg_ratings":
                pros = ServiceProfessional.query.filter(ServiceProfessional.avg_rating  >= search_input, ServiceProfessional.approval_status=="Approved").all()
                service_professionals = []
                for pro in pros:
                    service_professionals.append((pro, Services.query.filter_by(name=pro.service_type).first()))
                return render_template("customer_dashboard_search.html", service_professionals=service_professionals, last_input=search_input, filter_search=filter)
        all_pros = ServiceProfessional.query.filter_by(approval_status="Approved").all()
        service_professionals = []
        for pro in all_pros:
            service_professionals.append((pro, Services.query.filter_by(name=pro.service_type).first()))
        return render_template("customer_dashboard_search.html", service_professionals=service_professionals)
    else:
        flash("Unauthorized Access", "error")
        return redirect(url_for("home"))

# Customer Dashboard Summary
@app.route("/customer/dashboard/summary")
def customer_dashboard_summary():
    if Customer.query.filter_by(cust_id=session['user_id']).first() == None:
        flash("Unauthorised Access","error")
        return redirect(url_for("home"))
    else:
        x = ['Requested', 'Accepted', 'Closed']
        rec_req = len(ServiceRequest.query.filter_by(customer_id=session['user_id'], service_status="Requested").all())
        acc_req = len(ServiceRequest.query.filter_by(customer_id=session['user_id'], service_status="Accepted").all())
        clo_req = len(ServiceRequest.query.filter_by(customer_id=session['user_id'], service_status="Closed").all())
        y = [rec_req, acc_req,  clo_req]
        return render_template("customer_dashboard_summary.html", x=x, y=y)

## Logout

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__=="__main__":
    app.run(debug=True)


