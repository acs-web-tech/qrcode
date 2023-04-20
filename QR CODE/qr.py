import qrcode,io,base64
from PIL import Image
def generateQrCode(data:dict,base64flag=False):
  qr = qrcode.QRCode(version=1)
  qr.add_data(data)
  qr.make()
  img = qr.make_image()
  ioinp = io.BytesIO()
  img.save(ioinp,format=img.format)
  ioinp.seek(0)  
  if base64flag : 
    print(type( base64.b64encode(ioinp.getbuffer()).decode()))
    return ioinp.getvalue()
  else : 
    return ioinp
