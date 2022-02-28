# -*- codecs: utf-8 -*-
# -*- coding: cp1251 -*-
import codecs

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QPixmap
import sys
from ui import Ui_Form

import numpy as np
import cv2
import math
from scipy import ndimage
from keras.models import load_model

# Create application
app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon("егэ.ico"))
# Create form and init UI
Form = QtWidgets.QWidget()
ui = Ui_Form()
ui.setupUi(Form)
Form.show()

# Hook logic
def image_rotation(file_name):

    img_before = cv2.imread(file_name)

    img_gray = cv2.cvtColor(img_before, cv2.COLOR_BGR2GRAY)
    img_edges = cv2.Canny(img_gray, 100, 100, apertureSize=3)
    lines = cv2.HoughLinesP(img_edges, 1, math.pi / 180.0, 100, minLineLength=100, maxLineGap=5)

    angles = []

    for x1, y1, x2, y2 in lines[0]:
        # cv2.line(img_before, (x1, y1), (x2, y2), (255, 0, 0), 3)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        angles.append(angle)

    median_angle = np.median(angles)
    img_rotated = ndimage.rotate(img_before, median_angle)

    return img_rotated

def blank_reg_fio(file_name):
    img_before = cv2.imread(file_name)
    gray_image = cv2.cvtColor(img_before, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray_image, 140, 255, cv2.THRESH_BINARY)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    letters = []

    for idx, contour in enumerate(contours):
        (x, y, w, h) = cv2.boundingRect(contour)
        if hierarchy[0][idx][3] == 0:
            if ((w > 20) & (h > 40) & (y > 970) & (y < 1490)):
                letters.append((x - 7, y - 7, x + w + 7, y + h + 7))

    letters.sort(key=lambda x: x[1], reverse=False)

    answer = []
    k = 100
    for i in range(letters[0][1] // 100 + 1, letters[-1][3] // 100 + 1):
        ans = []
        for j in range(len(letters)):
            if ((k * i) <= letters[j][3] <= (k * (i + 1))):
                ans.append(letters[j])
            ans.sort(key=lambda x: x[0], reverse=False)
        answer.append(ans)

    classes = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н',
               'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э',
               'Ю', 'Я']
    model = load_model('letters.h5')
    fio = []

    for i in range(len(answer)):
        ans = ''
        for j in range(len(answer[i])):
            x = thresh[answer[i][j][1]:answer[i][j][3], answer[i][j][0]:answer[i][j][2]]  # yx
            x = cv2.resize(x, dsize=(28, 28))
            x = np.asarray(x, dtype='float64')
            x = 255 - x
            x /= 255.0
            x = x.reshape(1, 28, 28, 1)

            prediction = model.predict(x)
            prediction = classes[np.argmax(prediction)]
            ans += str(prediction)
        fio.append(ans)

    fio1 = ''
    for i in range(3):
        fio1 += fio[i]
        fio1 += ' '
    return fio1

def blank_otv_crop(img_rotated):
    gray_image = cv2.cvtColor(img_rotated, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray_image, 140, 255, cv2.THRESH_BINARY) #Бинаризация

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) #Выделение контуров
    letters = []

    for idx, contour in enumerate(contours):
        (x, y, w, h) = cv2.boundingRect(contour)
        if hierarchy[0][idx][3] == 0:
            if (w == 3) & (h == 3): # Поиск метки
                letters.append((x, y, x + w, y + h))

    letters.sort(key=lambda x: x[0], reverse=False)
    a = letters[0] # координата 1 метки
    b = letters[-1] # координата 2 метки
    crop = thresh[(a[0] + 703):(b[0] + 711), a[0]:b[0]] # Обрезка бланка
    return crop

def answer_column(letters):
    answer = []
    k = 100
    if (len(letters) > 0):
        for i in range(letters[-1][3] // 100 + 1):
            ans = []
            for j in range(len(letters)):
                if ((k * i) <= letters[j][3] <= (k * (i + 1))):
                    ans.append(letters[j])
                ans.sort(key=lambda x: x[0], reverse=False)
            answer.append(ans)
    return answer

def answer_blank(crop):
    contours, hierarchy = cv2.findContours(crop, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #output = crop.copy()
    letters_left = []
    letters_right = []

    for idx, contour in enumerate(contours):
        (x, y, w, h) = cv2.boundingRect(contour)
        if hierarchy[0][idx][3] == 0:
          if ((x > 80) & (x < 1100) & (h > 10) & (y < 1940)):
            #cv2.rectangle(output, (x - 10, y - 10), (x + w + 10, y + h + 10), (70, 0, 0), 1)
            letters_left.append((x - 7, y - 7, x + w + 7, y + h + 7))
          if ((x > 1235) & (h > 10) & (y < 1940)):
            #cv2.rectangle(output, (x - 10, y - 10), (x + w + 10, y + h + 10), (70, 0, 0), 1)
            letters_right.append((x - 10, y - 10, x + w + 10, y + h + 10))

    letters_left.sort(key=lambda x: x[1], reverse=False)
    letters_right.sort(key=lambda x: x[1], reverse=False)
    answer_left = answer_column(letters_left)
    answer_right = answer_column(letters_right)

    if (len(answer_left) < 20):
        for i in range(len(answer_left), 20):
            answer_left.append('')

    answer = answer_left + answer_right
    #cv2_imshow(output)
    return(answer)

def answer_blank_error(crop):
    contours, hierarchy = cv2.findContours(crop, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #output = crop.copy()
    letters_error_right = []
    letters_error_left = []

    for idx, contour in enumerate(contours):
        (x, y, w, h) = cv2.boundingRect(contour)
        if hierarchy[0][idx][3] == 0:
          if ((y > 2030) & (x < 1100) & (h > 10)):
            #cv2.rectangle(output, (x - 10, y - 10), (x + w + 10, y + h + 10), (70, 0, 0), 1)
            letters_error_left.append((x - 10, y - 10, x + w + 10, y + h + 10))
          if ((y > 2030) & (x > 1200) & (h > 10)):
            #cv2.rectangle(output, (x - 10, y - 10), (x + w + 10, y + h + 10), (70, 0, 0), 1)
            letters_error_right.append((x - 10, y - 10, x + w + 10, y + h + 10))

    letters_error_left.sort(key=lambda x: x[1], reverse=False)
    letters_error_right.sort(key=lambda x: x[1], reverse=False)
    answer_error_left = answer_column(letters_error_left)
    answer_error_right = answer_column(letters_error_right)
    z = answer_error_left + answer_error_right
    answer_error = [x for x in z if x]

    return(answer_error)

def predict(crop, answer, number_lesson):

    answer_blank = []
    classes = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н',
               'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э',
               'Ю', 'Я']

    for i in range(len(answer)):
        if (i in number_lesson):
            model = load_model("letters.h5")
            letters = True
        else:
            model = load_model("cnn_digits_28x28.h5")
            letters = False
        ans = ''
        for j in range(len(answer[i])):
            x = crop[answer[i][j][1]:answer[i][j][3], answer[i][j][0]:answer[i][j][2]]  # yx
            x = cv2.resize(x, dsize=(28, 28))
            x = np.asarray(x, dtype='float64')
            x = 255 - x
            x /= 255.0
            x = x.reshape(1, 28, 28, 1)

            prediction = model.predict(x)
            prediction = np.argmax(prediction)
            if (letters == False):
                ans += str(prediction)
            else:
                ans += str(classes[prediction])
        answer_blank.append(ans)

    return answer_blank

def lesson(lesson):
    a = []
    if (lesson == "Русский язык"):
        a = [1, 3, 4, 5, 6, 12, 13, 22]
    if ((lesson == "Обществознание") | (lesson == "Биология")):
        a = [0, 1]
    if (lesson == "География"):
        a = [0, 23, 24]
    if (lesson == "Литература"):
        a = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13]
    if (lesson == "История"):
        a = [3, 9, 12, 13, 14]
    return a

def download_answer():
    try: #Файл выбран
        file_name = QFileDialog.getOpenFileName() #Считывание имени файла
        f = codecs.open(file_name[0], "r", "utf-8") #Открытие файла
        answer = f.readlines() #Считывание ответов из файла
        ui.tableWidget.setRowCount(len(answer)) #Созданите столбцов в таблице
        for i in range(len(answer)):
            ui.tableWidget.setItem(i, 0, QTableWidgetItem(str(answer[i].strip()))) #Запись ответов в таблицу
        f.close()
    except OSError: #Файл не выбран
        error = QMessageBox()
        error.setWindowTitle('Ошибка')
        error.setText('Вы не выбрали файл!')
        error.setIcon(QMessageBox.Critical)
        error.setStandardButtons(QMessageBox.Ok)
        error.exec_()

def download_blanks():

    if ui.lineEdit.text(): #Проверка ввода кол-ва учеников
        file_name = QFileDialog.getOpenFileNames() #Имена файлов
        patch = open("file_name.txt", 'w') #Создание файла для записи
        k = int(ui.lineEdit.text()) * 2

        if (len(file_name[0]) > 0) & (len(file_name[0]) == k):
            ok = QMessageBox()
            ok.setWindowTitle('OK')
            ok.setText('Файлы успешно загружены!')
            ok.setIcon(QMessageBox.Information)
            ok.setStandardButtons(QMessageBox.Ok)
            ok.exec_()

            for i in range(k):
                patch.write(str(file_name[0][i]) + '\n') #Запись путей к бланкам
        else:
            error = QMessageBox()
            error.setWindowTitle('Ошибка')
            error.setText('Вы не выбрали файлы или выбрали бланки не всех учеников!')
            error.setIcon(QMessageBox.Critical)
            error.setStandardButtons(QMessageBox.Ok)
            error.exec_()
    else:
        error = QMessageBox()
        error.setWindowTitle('Ошибка')
        error.setText('Введите количество учеников!')
        error.setIcon(QMessageBox.Critical)
        error.setStandardButtons(QMessageBox.Ok)
        error.exec_()

fio_list = []
score_list = []
answer_list = []
number_student = [0]
answer_check = []

def check():
    fio_list.clear()
    score_list.clear()
    answer_list.clear()
    answer_check.clear()
    number_student[0] = 0
    ui.tableWidget_2.setRowCount(int(ui.lineEdit.text()))
    ui.tableWidget_3.setRowCount(ui.tableWidget.model().rowCount())
    lesson_ = ui.comboBox.currentText()
    number_lesson = lesson(lesson_)
    answer = []

    row_numder = 0

    for i in range(ui.tableWidget.model().rowCount()):
        answer.append(ui.tableWidget.item(i, 0).text())

    patch_blanks = open("file_name.txt", "r")
    file_blanks = patch_blanks.readlines()

    number_blank = int(ui.lineEdit.text()) * 2

    for i in range(0, number_blank, 2):
        fio = blank_reg_fio(file_blanks[i].strip())
        crop = blank_otv_crop(image_rotation(file_blanks[i+1].strip()))
        answer_blank_ = predict(crop, answer_blank(crop), number_lesson)
        answer_error = predict(crop, answer_blank_error(crop), number_lesson)

        if (len(answer_error) > 0):
            for i in range(len(answer_error)):
                index = int(answer_error[i][:2]) - 1
                char = answer_error[i][2:]
                answer_blank_[index] = char

        i1 = 0 # ,-
        for ans in answer:
            if '-' in ans:
                answer_blank_[i1] = '-' + answer_blank_[i1][1:]
            if ',' in ans:
                find = ans.find(',')
                answer_blank_[i1] = answer_blank_[i1][:find] + ',' + answer_blank_[i1][find + 1:]
            i1 += 1

        answer_list.append(answer_blank_)

        score = 0 # Количетво правильных
        answ = []
        for i1 in range(len(answer)):
            if (answer[i1] == answer_blank_[i1]):
                score += 1
                answ.append(i1)
        answer_check.append(answ)

        ui.tableWidget_2.setItem(row_numder, 0, QTableWidgetItem(fio))
        ui.tableWidget_2.setItem(row_numder, 1, QTableWidgetItem(str(score)))
        row_numder += 1
        fio_list.append(fio)
        score_list.append(score)

    ui.label_4.setText(fio_list[number_student[0]])

    pixmap = QPixmap(file_blanks[number_student[0]+1].strip())
    ui.label_6.setPixmap(pixmap.scaled(491, 501, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation))
    patch_blanks.close()

    for i in range(ui.tableWidget.model().rowCount()):
        ui.tableWidget_3.setItem(i, 0, QTableWidgetItem(answer_list[number_student[0]][i]))
        if i not in answer_check[0]:
            ui.tableWidget_3.item(i, 0).setBackground(QtGui.QColor(255, 0, 0))
    ui.lineEdit_2.setText(str(score_list[number_student[0]]))

def down():
    patch_blanks = open("file_name.txt", "r")
    file_blanks = patch_blanks.readlines()
    if ((number_student[0] - 1) >= 0):
        number_student[0] -= 1
        ui.label_4.setText(fio_list[number_student[0]])

        if (number_student[0] == 0):
            pixmap = QPixmap(file_blanks[number_student[0] + 1].strip())
        else:
            pixmap = QPixmap(file_blanks[number_student[0] + 2].strip())
        ui.label_6.setPixmap(pixmap.scaled(491, 501, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation))
        patch_blanks.close()

        for i in range(ui.tableWidget.model().rowCount()):
            ui.tableWidget_3.setItem(i, 0, QTableWidgetItem(answer_list[number_student[0]][i]))
            if i not in answer_check[number_student[0]]:
                ui.tableWidget_3.item(i, 0).setBackground(QtGui.QColor(255, 0, 0))
        ui.lineEdit_2.setText(str(score_list[number_student[0]]))
    patch_blanks.close()

def next():
    patch_blanks = open("file_name.txt", "r")
    file_blanks = patch_blanks.readlines()
    if ((number_student[0] + 1) < (len(file_blanks) / 2)):
        number_student[0] += 1
        ui.label_4.setText(fio_list[number_student[0]])

        pixmap = QPixmap(file_blanks[number_student[0] + 2].strip())
        ui.label_6.setPixmap(pixmap.scaled(491, 501, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation))
        patch_blanks.close()

        for i in range(ui.tableWidget.model().rowCount()):
            ui.tableWidget_3.setItem(i, 0, QTableWidgetItem(answer_list[number_student[0]][i]))
            if i not in answer_check[number_student[0]]:
                ui.tableWidget_3.item(i, 0).setBackground(QtGui.QColor(255, 0, 0))
        ui.lineEdit_2.setText(str(score_list[number_student[0]]))
    patch_blanks.close()
# Run main loop
ui.pushButton.clicked.connect(download_answer)
ui.pushButton_2.clicked.connect(download_blanks)
ui.pushButton_3.clicked.connect(check)
ui.pushButton_4.clicked.connect(down)
ui.pushButton_5.clicked.connect(next)

sys.exit(app.exec_())

#f = open("file_name.txt", "r")
#blank = f.readlines()
#pixmap = QPixmap(blank[0].strip())
#ui.label_6.setPixmap(pixmap.scaled(491, 501, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation))
#f.close()