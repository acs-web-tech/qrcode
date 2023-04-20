import cv2 as cv
def scan(imageurl):
  img  = cv.imread(imageurl)
  detector = cv.QRCodeDetector()
  value,point,slices = detector.detectAndDecode(img) 
  print(value)
  return value