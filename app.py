from flask import Flask, render_template, Response, redirect, url_for, send_from_directory
import cv2
import os
from cvzone.PoseModule import PoseDetector
import cvzone

app = Flask(__name__)


cap = cv2.VideoCapture(0)
detector = PoseDetector()
shirtFolderPath = "resources/newShirts"  
listShirts = os.listdir(shirtFolderPath)
fixedRatio = 262 / 190
shirtRatioHeightWidth = 581 / 440
imageNumber = 0

imgButtonRight = cv2.imread("resources/button.png", cv2.IMREAD_UNCHANGED)  
imgButtonLeft = cv2.flip(imgButtonRight, 1)
buttonWidth, buttonHeight = imgButtonRight.shape[1] // 2, imgButtonRight.shape[0] // 2
imgButtonRight = cv2.resize(imgButtonRight, (buttonWidth, buttonHeight))
imgButtonLeft = cv2.resize(imgButtonLeft, (buttonWidth, buttonHeight))

counterRight = 0
counterLeft = 0
selectionSpeed = 10

def generate_frames():
    global imageNumber, counterRight, counterLeft
    while True:
        success, img = cap.read()
        if not success:
            break
        else:
            img = detector.findPose(img, draw=False)
            lmList, bboxInfo = detector.findPosition(img, bboxWithHands=False, draw=False)
            if lmList:
                lm11 = lmList[11][1:3]
                lm12 = lmList[12][1:3]
                imgShirt = cv2.imread(os.path.join(shirtFolderPath, listShirts[imageNumber]), cv2.IMREAD_UNCHANGED)
                widthOfShirt = int((lm11[0] - lm12[0]) * fixedRatio)
                if widthOfShirt > 0:
                    imgShirt = cv2.resize(imgShirt, (widthOfShirt, int(widthOfShirt * shirtRatioHeightWidth)))
                    currentScale = (lm11[0] - lm12[0]) / 190
                    offset = int(44 * currentScale), int(48 * currentScale)
                    try:
                        img = cvzone.overlayPNG(img, imgShirt, (lm12[0] - offset[0], lm12[1] - offset[1]))
                    except:
                        pass

                    img = cvzone.overlayPNG(img, imgButtonRight, (510, 175))
                    img = cvzone.overlayPNG(img, imgButtonLeft, (59, 175))

                    if lmList[16][1] < 150:
                        counterRight += 1
                        cv2.ellipse(img, (90, 205), (33, 33), 0, 0, counterRight * selectionSpeed, (0, 255, 0), 9)
                        if counterRight * selectionSpeed > 360:
                            counterRight = 0
                            if imageNumber < len(listShirts) - 1:
                                imageNumber += 1
                    elif lmList[15][1] > 450:
                        counterLeft += 1
                        cv2.ellipse(img, (540, 205), (33, 33), 0, 0, counterLeft * selectionSpeed, (0, 255, 0), 9)
                        if counterLeft * selectionSpeed > 360:
                            counterLeft = 0
                            if imageNumber > 0:
                                imageNumber -= 1
                    else:
                        counterRight = 0
                        counterLeft = 0

            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/try_on', methods=['GET'])
def try_on():
    return render_template('try_on.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/outfits')
def outfits():
    shirts = os.listdir(shirtFolderPath)
    return render_template('outfits.html', shirts=shirts)

@app.route('/resources/newShirts/<filename>')
def shirt_image(filename):
    return send_from_directory(shirtFolderPath, filename)

if __name__ == "__main__":
    app.run(debug=True)
