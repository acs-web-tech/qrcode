import smtplib,qr,base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def mailer(recivier:str,secret:str):
  s = smtplib.SMTP('smtp.gmail.com', 587)
  mimetype = MIMEMultipart()
  mimetype['Subject'] = "QR AUTH"
  mimetype["Form"] = "agencyarun5@gmail.com"
  mimetype["To"] = recivier
  file =MIMEImage(qr.generateQrCode(secret,base64flag=True))
  file.add_header("Content-Disposition", "attachment",filename="qr.png")
  mimetype.attach(file)
  message = """
  <html>
  <body>
<h2>Scan the following QR CODE TO VERIFY YOUR EMAIL ADDRESS</h2>

</body>
</html>
"""
  print(message)
  s.starttls()
  s.login("agencyarun5@gmail.com", "qgkjagrmsfvrpgnz")
  if not s.sendmail("agencyarun5@gmail.com", recivier,mimetype.as_string()) :
    s.quit()
    return True
  else :
    return False
  
