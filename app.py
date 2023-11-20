from flask import Flask,render_template,redirect,request,session,url_for,flash
import pymysql,secrets,random,re
from flask_mail import Mail,Message

app=Flask(__name__)

app.secret_key="ltobby"

connection=pymysql.connect(
                host='localhost',
                user='root',
                password='',
                database='ubuntu'
            )

app.config["MAIL_SERVER"]='smtp.gmail.com'
app.config["MAIL_PORT"]=465
app.config["MAIL_USERNAME"]='tobiaskipkogei@gmail.com'
app.config["MAIL_PASSWORD"]='himfefhwbqyfhekg'
app.config["MAIL_USE_TLS"]=False
app.config["MAIL_USE_SSL"]=True
mail=Mail(app)

def generate_otp():
    return ''.join(random.choices('0123456789',k=6))

@app.route("/register",methods=['POST','GET'])
def register():
    if 'name' in session:
        return redirect(url_for('home'))
    else:
        if request.method=='POST':
            name=request.form['name']
            email=request.form['email']
            password=request.form['password']
            confirm=request.form['confirm']
            cur=connection.cursor()
            cur.execute("SELECT * FROM users WHERE name=%s",(name))
            connection.commit()
            data=cur.fetchone()
            if data:
                flash("This username already exits")
                return redirect(url_for('register'))
            else:
                cur=connection.cursor()
                cur.execute("SELECT * FROM users WHERE email=%s",(email))
                connection.commit()
                data=cur.fetchone()
                if data:
                    flash(f"This email already has an account registered","danger")
                    return redirect(url_for('register'))
                elif password!= confirm :
                    flash(f"Passwords doesn't match","danger")
                    return redirect(url_for('register'))
                elif len(password) < 8:
                    flash(f"password must be more than 8 characters!","danger")
                    return render_template('register.html', name=name, email=email,password=password)
                elif not re.search("[a-z]", password):
                    flash(f"password must have small letters!","danger")
                    return render_template('register.html', name=name, email=email,password=password)
                elif not re.search("[A-Z]", password):
                    flash(f"password must have capital letters!","danger")
                    return render_template('register.html', name=name, email=email,password=password)
                elif not re.search("[_@$]+", password):
                    flash(f"Password must contain special characters!","danger")
                    return render_template('register.html', name=name, email=email, password=password)
                else:
                    verify=0
                    otp=generate_otp()
                    cur=connection.cursor()
                    cur.execute("INSERT INTO users(name,email,password,otp,verify)VALUES(%s,%s,%s,%s,%s)",(name,email,password,otp,verify))
                    connection.commit()
                    cur.close()
                    msg=Message (subject='Account creation',sender="tobiaskipkogei@gmail.com" ,recipients=[email])
                    msg.body=f"""Your have succesfully created and account at our page
                                your USERNAME is{name}
                                And Password is*{password}*
                                """
                    mail.send(msg)
                    send_otp(email,otp)
                    flash(f"OTP sent to your email","warning")
                    return redirect('verify_otp')
    return render_template("register.html")

@app.route("/send_otp",methods=['POST','GET'])
def send_otp(email,otp): 
    msg=Message(subject='Your OTP' ,sender="tobiaskipkogei@gmail.com",recipients=[email])
    msg.body=f'Your otp is:{otp}'
    mail.send(msg)
    

@app.route("/verify_otp",methods=['POST','GET'])
def verify_otp():
    if request.method=='POST':
        user_otp=request.form['user_otp']
        cur=connection.cursor()
        cur.execute("SELECT * FROM users WHERE otp=%s",(user_otp))
        connection.commit()
        data=cur.fetchone()
        if data:
            verify=1
            cur=connection.cursor()
            cur.execute("UPDATE users SET verify=%s WHERE otp=%s",(verify,user_otp))
            connection.commit()
            cur.close()
            flash(f"OTP verified!","success")
            return redirect(url_for('login'))
        else:
            flash(f"Invalid OTP.Please try again.","danger")
            return redirect(url_for("verify_otp"))
    return  render_template("otp.html")

@app.route("/login",methods=['POST','GET'])
def login(): 
    if 'name' in session:
        return redirect(url_for('home'))
    else:
        if request.method=="POST":
            name=request.form['name']
            password=request.form['password']
            cur=connection.cursor()
            cur.execute("SELECT * FROM users WHERE name=%s AND password=%s",(name,password))
            connection.commit()
            data=cur.fetchone()
            cur.close()
            if data is not None:
                is_verified=int(data[6])
                if is_verified==1:
                    session['name']=data[1]
                    session['id']=data[0]
                    return redirect(url_for('home'))
                else:
                    return redirect(url_for('verify_otp'))
            else:
                flash(f"No user with that account","danger")
                return render_template("login.html",name=name,password=password)
    return render_template("login.html")


@app.route("/forgotpassword",methods=['POST','GET'])
def forgotpassword():
    if request.method=='POST':
        email=request.form['email']
        cur=connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s",(email,))
        connection.commit()
        data=cur.fetchone()
        if data :
            token=secrets.token_hex(16)
            reset_link=url_for('reset',token=token,_external=True)
            msg=Message(subject='Password reset',sender='tobiaskipkogei@gmail.com',recipients=[email])
            msg.body=f"Your are about to reset your password Click the following link to reset your password:{reset_link}"
            mail.send(msg)
            cur=connection.cursor()
            cur.execute("UPDATE users set token=%s where email=%s",(token,email))
            connection.commit()
            cur.close()
            flash(f'Reset link has been sent to your email',"success")
            return redirect(url_for('forgotpassword'))
        else:
            flash(f"We can't find your email in our system","warning")
            return redirect(url_for('forgotpassword'))

    return render_template("forgotpassword.html")

# reset pasword
@app.route("/reset",methods=['POST','GET'])
def reset():
    if request.method=="POST":
        new_password=request.form['password']
        confirm=request.form['confirm']
        token=request.args.get('token')
        if new_password != confirm:
            flash(f"Your password do not match","danger")
            return render_template('reset.html',password=new_password,confirm=confirm)
        elif len(new_password) < 8:
            flash(f"password must be more than 8 characters!","danger")
            return render_template('reset.html',password=new_password,confirm=confirm)
        elif not re.search("[a-z]",new_password):
            flash(f"password must have small letters!","danger")
            return render_template('reset.html',password=new_password,confirm=confirm)
        elif not re.search("[A-Z]",new_password):
            flash(f"password must have capital letters!","danger")
            return render_template('reset.html',password=new_password,confirm=confirm)
        elif not re.search("[_@$]+",new_password):
            flash(f"Password must contain special characters!","danger")
            return render_template('reset.html',password=new_password,confirm=confirm)
        else:
            cur=connection.cursor()
            cur.execute("UPDATE users SET password=%s AND token='token' WHERE token=%s",(new_password,token))
            connection.cursor()
            cur.close()
            return render_template('login.html',success='You have  succefully reset your password')
    return render_template("reset.html")


@app.route('/wantto_log')
def wantto_log():
    return render_template("wantto_log.html")
@app.route('/yes')
def yes():
    session.clear()
    flash(f" Your have been logged out successfully ","success")
    return redirect(url_for('login'))

@app.route("/no",methods=['POST','GET'])
def no():
    return render_template("home.html")

@app.route("/home",methods=['POST','GET'])
def home():
    return render_template("home.html")

@app.route("/menu",methods=['POST','GET'])
def menu():
    if request.method=='POST':
        message=request.form['message']
        location=request.form['location']
        date=request.form['date']
        time=request.form['time']
        duration=request.form['duration']
        cur=connection.cursor()
        cur.execute("SELECT * FROM schedule WHERE date=%s ",(date))
        connection.commit()
        data=cur.fetchone()
        if data:
            if data[3]==time :
                flash(f"The  time has been allocated to another event","danger")
                return redirect(url_for("menu"))
        else:
            cur=connection.cursor()
            cur.execute("INSERT INTO schedule(message,location,date,time,duration) VALUES(userid)",(message,location,date,time,duration))
            connection.commit()
            cur.close()
            flash(f"events updated","success")
            return render_template("schedule.html")
    return render_template("menu.html")

@app.route("/schedule",methods=['POST','GET'])
def schedule():
    if "name" in session:
        cur=connection.cursor()
        cur.execute("SELECT * FROM schedule")
        connection.commit()
        data=cur.fetchall()
        return render_template("schedule.html",data=data)
    return render_template("schedule.html")

# Define a custom error handler for 404 Not Found
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# Define a custom error handler for 500 Internal Server Error
@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500

@app.route('/index')
def index():
    # Simulate a 404 error
    return "This page does not exist", 404

@app.route('/error')
def error():
    # Simulate a 500 error
    1 / 0




if __name__=="__main__":
    app.run(debug=True)
