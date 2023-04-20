from flask import Flask,render_template, request,send_file, redirect, session, flash, make_response,url_for
from functools import wraps
from flask_mysqldb import MySQL
import qrcode
import os,jwt,mailer,scan
import cv2 as cv
from datetime import datetime
import shutil
import mimetypes


app = Flask(__name__,static_url_path="/static")
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'QR'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

#app.config['UPLOAD_FILES'] = "static/files"


@app.route('/')
@app.route('/login', methods=['POST', 'GET'])
def login():
    status = True
    if request.method == 'POST':
        email = request.form["email"]
        pwd = request.form["upass"]
        cur = mysql.connection.cursor()
        cur.execute(
            "select * from users where EMAIL=%s and UPASS=%s", (email, pwd))
        data = cur.fetchone()
        if data:
            session['logged_in'] = True
            session['username'] = data["UNAME"]
            flash('Login Successfully', 'success')
            return redirect('home')
        else:
            flash('Invalid Login. Try Again', 'danger')
    return render_template("login.html")


@app.route('/adminlogin', methods=['POST', 'GET'])
def adminlogin():
    status = True
    if request.method == 'POST':
        email = request.form["email"]
        pwd = request.form["upass"]
        if email == pwd == "Admin":
            flash('Login Successfully', 'success')
            return redirect('userslist')
        else:
            flash('Invalid Login. Try Again', 'danger')
    return render_template("adminlogin.html")


@app.route('/userslist', methods=['POST', 'GET'])
def userslist():
    cur = mysql.connection.cursor()
    cur.execute("select * from users")
    data = cur.fetchall()
    return render_template("userslist.html", datas=data)


@app.route('/qrgen', methods=['POST', 'GET'])
def qrgen():
    img = qrcode.make(session["username"])
    img.save('static/' + session["username"] + '.jpg')
    img.save('static/QR/' + session["username"] +
             '/' + session["username"] + '.jpg')
    flash('QR Created Successfully', 'success')
    return redirect("viewqr")


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)

    return wrap


@app.route('/reg', methods=['POST', 'GET'])
def reg():
    status = False
    if request.method == 'POST':
        name = request.form["uname"]
        email = request.form["email"]
        pwd = request.form["upass"]
        mobile = request.form["mobile"]
        cur = mysql.connection.cursor()
        cur.execute(
            "insert into users(UNAME,UPASS,EMAIL,MOBILE) values(%s,%s,%s,%s)", (name, pwd, email, mobile))
        mysql.connection.commit()
        cur.close()
        os.mkdir("static/QR/"+name)
        flash('Registration Successfully. Login Here...', 'success')
        return redirect('login')
    return render_template("reg.html", status=status)


@app.route("/sendfile")
def sendfile():
    cur = mysql.connection.cursor()
    cur.execute('SELECT UID, UNAME FROM users')
    joblist = cur.fetchall()
    return render_template('sendfile.html', joblist=joblist)


@app.route("/sending", methods=['POST', 'GET'])
def sending():
    status = True
    if request.method == 'POST':
        now = datetime.now()
        accesskey = os.urandom(12).hex()
        receiver = request.form["sender"]
        username = session["username"]
        filedec = request.form["filedec"]
        filename = request.files['uploadfile']

        if receiver != username:
            app.config['UPLOAD_FILES'] = "static/QR/" + session["username"]
            if filename.filename != '':
                filepath = os.path.join(
                    app.config['UPLOAD_FILES'], filename.filename)
                filename.save(filepath)

                key1 = os.urandom(12).hex()
                buffersize = 64 * 1024

                cur = mysql.connection.cursor()
                cur.execute("insert into upload(username, receiver, filename, filedec, filepath, fileaccesskey, datetime) values (%s,%s,%s,%s,%s,%s,%s)",
                            (username, receiver, filename.filename, filedec, "static/QR/" + session["username"] + "/" + filename.filename, accesskey, now))
                mysql.connection.commit()
                cur.close()
                cur = mysql.connection.cursor()
                cur.execute('SELECT UID, UNAME FROM users')
                joblist = cur.fetchall()
                cur.close()
                cur = mysql.connection.cursor()
                encodedata =  jwt.encode({'reciver':receiver,"key":accesskey},"rrrfrjrkrfkjj")
                cur.execute("select EMAIL from users where UNAME=%s",(receiver,))
                mysql.connection.commit()
                email = cur.fetchall()
                print(email)
                mailer.mailer(email[0]['EMAIL'],encodedata)
                cur.close()
                flash('File Uploaded Successfully', 'success')
              
                return render_template('sendfile.html', joblist=joblist)
            else:
                flash('Error in File Upload! Try Again', 'danger')
        else:
            flash('Please Select a Valid User! Try Again', 'danger')
    cur = mysql.connection.cursor()
    cur.execute('SELECT UID, UNAME FROM users')
    joblist = cur.fetchall()
    return render_template('sendfile.html', joblist=joblist)


@app.route('/receivefile', methods=['POST', 'GET'])
def receivefile():
    cur = mysql.connection.cursor()
    cur.execute("select * from upload where receiver='" +
                session["username"] + "'")
    data = cur.fetchall()
    return render_template("receivefile.html", datas=data)


@app.route('/<string:fileaccesskey>/userdownloadrequest', methods=['POST', 'GET'])
def userdownloadrequest(fileaccesskey):
    cur = mysql.connection.cursor()
    cur.execute("select * from upload where receiver='" +
                session["username"] + "' and fileaccesskey = '" + fileaccesskey + "'")
    data = cur.fetchone()
    filename = data["filename"]
    sender = data["username"]
    ms = "Sender : " + sender + " Receiver : " + \
        session["username"] + " File Name : " + filename
    img = qrcode.make(ms)
    img.save('static/' + session["username"] + '_2LQR.jpg')

    cur.execute("select * from upload where receiver='" +
                session["username"] + "'")
    data1 = cur.fetchall()

    cur.close()
    imgg = session["username"] + '_2LQR.jpg'
    return render_template("receivefile.html", img=imgg, datas=data1)


@app.route('/<string:fileaccesskey>/decode', methods=['POST', 'GET'])
def decode(fileaccesskey):
    cur = mysql.connection.cursor()
    cur.execute("select * from upload where receiver='" +
                session["username"] + "' and fileaccesskey = '" + fileaccesskey + "'")
    data = cur.fetchone()
    filename = data["filename"]
    sender = data["username"]
    ms = "Sender : " + sender + " Receiver : " + \
        session["username"] + " File Name : " + filename
    shutil.copy2('static/QR/' + sender + "/" + filename,
                 'static/QR/' + session["username"])
    cur.execute("select * from upload where receiver='" +
                session["username"] + "'")
    data1 = cur.fetchall()

    cur.close()
    return render_template("receivefile.html", datas=data1)


@ app.route("/viewqr")
def viewqr():
    imgg = session["username"] + '.jpg'
    return render_template('viewqr.html', img=imgg)


@ app.route("/home")
@ is_logged_in
def home():
    return render_template('home.html')


@ app.route("/logout")
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route("/check",methods=['POST'])
def qr():
     if  session['logged_in']:
         file = request.files['file']
         path =os.path.join(os.getcwd()+"/temp/" ,session['username']+".png")
         file.save(path)
         key = scan.scan(path)
         try:
                decoded = jwt.decode(key,"rrrfrjrkrfkjj", algorithms=["HS256"])
                if session['username'] == decoded['reciver']:
                   
                   cur  = mysql.connection.cursor()
                   cur.execute("select filepath from upload where fileaccesskey=%s",[decoded['key'],])
                   mysql.connection.commit()
                   fetch = cur.fetchall()
                   cur.close()
                   response  = make_response( send_file(fetch[0]['filepath'],as_attachment=True))
                   mime_type,encoding = mimetypes.guess_type('C:/Users/Admin/Downloads/QR CODE/'+fetch[0]['filepath'])
                   response.headers['Content-Type'] = mime_type
                   print('C:/Users/Admin/Downloads/OR CODE/'+fetch[0]['filepath'])
                   os.remove(path)
                   return response
                else : 
                    os.remove(path)
                    return "Access denied"
         except Exception as e:
            print(e)
            os.remove(path)
            return '500'
     return ""     
#    #key = scan.scan(request.get_json())
#    cur = mysql.connection.cursor()
#    cur.execute("select UNAME,fileaccesskey,filepath from upload where UNAME=%s and fileaccesskey=%s",[session['username'],key])
#    mysql.connection.commit()
#    data = cur.fetchAll()
#    cur.close()
#    if key == key['key']:
#        redirect(data[0]['filepath'])       
#    else :
#        flash("Invalid Access Details",'danger')
if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
