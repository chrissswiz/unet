
import sys

import cv2
from PyQt5 import Qt
from PyQt5.QtGui import QIcon, QBrush, QPainter, QPen, QPixmap, QColor, QImage, QGuiApplication
from PyQt5.QtWidgets import (
    QFileDialog,
    QApplication,
    QGraphicsEllipseItem,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QShortcut,
    QMessageBox,
    QGraphicsScene,
    QGraphicsView,
    QLabel, QDesktopWidget,
)
import numpy as np
from skimage import io
import time
from PIL import Image
from unet import Unet
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QSplitter


# 创建Unet实例，替换为您的模型路径和参数
model_path = 'logs3/best_epoch_weights.pth'
num_classes = 2
unet_instance = Unet(model_path=model_path, num_classes=num_classes,input_shape=[256, 256])

# 创建Unet实例，替换为您的模型路径和参数
model_path = 'logs4/best_epoch_weights.pth'
num_classes = 2
unet_instance1 = Unet(model_path=model_path, num_classes=num_classes,input_shape=[1024, 1024])

def np2pixmap(np_img):
    height, width, channel = np_img.shape
    bytesPerLine = 3 * width
    qImg = QImage(np_img.data, width, height, bytesPerLine, QImage.Format_RGB888)
    return QPixmap.fromImage(qImg)

colors = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (128, 0, 0),
    (0, 128, 0),
    (0, 0, 128),
    (128, 128, 0),
    (128, 0, 128),
    (0, 128, 128),
    (255, 255, 255),
    (192, 192, 192),
    (64, 64, 64),
    (0, 0, 127),
    (192, 0, 192),
]

class MaterialButton(QPushButton):
    def __init__(self, text, parent=None):
        super(MaterialButton, self).__init__(text, parent)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #3F51B5; /* Material Design Blue 500 */
                color: white;
                border-radius: 10px; /* Increase border radius for larger buttons */
                padding: 15px 20px; /* Increase padding for larger buttons */
                font-size: 16px; /* Increase font size for larger buttons */
            }
            QPushButton:hover {
                background-color: #303F9F; /* Material Design Blue 700 */
            }
            """
        )


class Window(QMainWindow):

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ShiftModifier:
            zoom_factor = 1.15  # 缩放因子，你可以根据需要调整
            if event.angleDelta().y() > 0:
                # 向上滚动鼠标滚轮，放大图片
                self.view1.scale(zoom_factor, zoom_factor)
            else:
                # 向下滚动鼠标滚轮，缩小图片
                self.view1.scale(1 / zoom_factor, 1 / zoom_factor)
        else:
            # 如果没有按住 Shift 键，则执行默认的滚轮事件
            super().wheelEvent(event)
        if event.modifiers() & Qt.ControlModifier:
            zoom_factor = 1.15  # 缩放因子，你可以根据需要调整
            if event.angleDelta().y() > 0:
                # 向上滚动鼠标滚轮，放大图片
                self.view2.scale(zoom_factor, zoom_factor)
            else:
                # 向下滚动鼠标滚轮，缩小图片
                self.view2.scale(1 / zoom_factor, 1 / zoom_factor)
        else:
            # 如果没有按住 Shift 键，则执行默认的滚轮事件
            super().wheelEvent(event)

    def __init__(self):
        super().__init__()

        # configs
        self.half_point_size = 5
        self.line_width=5
        # app stats
        self.image_path = None
        self.color_idx = 0
        self.bg_img = None
        self.is_mouse_down = False
        self.rect = None
        self.point_size = self.half_point_size * 2
        self.start_point = None
        self.end_point = None
        self.start_pos = (None, None)
        self.mask_c = np.zeros((1024, 1024, 3), dtype="uint8")
        self.coordinate_history = []
        self.history = []  # 历史记录
        self.mode = "draw"  # 当前模式，默认为绘制模式
        self.restore_region_history = {}  # 恢复区域的历史记录
        self.initial_image = None  # 记录最初图片的样子
        self.view1 = QGraphicsView()
        self.view2 = QGraphicsView()
        self.img_3c_view1 = None
        self.img_3c_view2 = None

        # 创建QSplitter以容纳两个视图
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.view1)
        splitter.addWidget(self.view2)
        self.setCentralWidget(splitter)  # 设置QSplitter为主窗口的中央组件

        self.view = QGraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setMouseTracking(True)

        # 确保在初始化方法中设置了正确的滚动区域，以便可以滚动查看整个图像
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)


        pixmap = QPixmap(1024, 1024)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.view)


        load_button = MaterialButton("加载图片")
        save_button = MaterialButton("保存mask")
        undo_button = MaterialButton("返回上一步")
        draw_button = MaterialButton("drwa模式")
        restore_button = MaterialButton("restore模式")
        difference_button = MaterialButton("difference模式")
        edge_button = MaterialButton("描边")
        delete_button = MaterialButton("无规则删除")
        # history_button = MaterialButton("查看历史记录")
        # toggle_mode_button = MaterialButton("切换模式")  # 切换模式按钮

        # 设置初始窗口状态为普通大小窗口，而不是全屏
       # 获取屏幕的大小和任务栏高度
        desktop = QDesktopWidget()
        screen_geometry = desktop.screenGeometry(desktop.primaryScreen())
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        taskbar_height = desktop.availableGeometry().height() - screen_geometry.height()

        # 设置窗口初始位置和大小，以避免覆盖任务栏
        self.setGeometry(0, 0, screen_width, screen_height - taskbar_height -112)

        hbox = QHBoxLayout(self)
        hbox.addWidget(load_button)
        hbox.addWidget(save_button)
        hbox.addWidget(undo_button)
        hbox.addWidget(draw_button)
        hbox.addWidget(restore_button)
        hbox.addWidget(difference_button)
        hbox.addWidget(edge_button)
        hbox.addWidget(delete_button)
        # hbox.addWidget(history_button)
        # hbox.addWidget(toggle_mode_button)  # 将切换模式按钮添加到水平布局中

        vbox.addLayout(hbox)

        self.setLayout(vbox)

        self.quit_shortcut = QShortcut("Esc", self)
        self.quit_shortcut.activated.connect(self.quit)

        load_button.clicked.connect(self.load_image)
        save_button.clicked.connect(self.save_mask)
        undo_button.clicked.connect(self.undo_last_edit)
        draw_button.clicked.connect(self.draw_mode)
        restore_button.clicked.connect(self.restore_mode)
        difference_button.clicked.connect(self.difference_mode)
        edge_button.clicked.connect(self.toggle_edge_mode)
        delete_button.clicked.connect(self.delete_edge)

        # history_button.clicked.connect(self.view_history)
        # toggle_mode_button.clicked.connect(self.toggle_mode)  # 连接切换模式按钮的点击事件
        toolbar = self.addToolBar("Tools")
        toolbar.addWidget(load_button)
        toolbar.addWidget(save_button)
        toolbar.addWidget(undo_button)
        toolbar.addWidget(restore_button)
        toolbar.addWidget(draw_button)
        toolbar.addWidget(difference_button)
        toolbar.addWidget(edge_button)
        toolbar.addWidget(delete_button)


    def quit(self):
        QApplication.quit()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", ".", "Image Files (*.png *.jpg *.bmp)"
        )

        if not file_path:
            print("未指定图像路径，请选择一个图像")
            return

        img_np = io.imread(file_path)
        if len(img_np.shape) == 2:
            img_3c = np.repeat(img_np[:, :, None], 3, axis=-1)
        else:
            img_3c = img_np

        max_width = 9999
        max_height = 99999
        if img_3c.shape[0] > max_height or img_3c.shape[1] > max_width:
            img_3c = self.resize_image(img_3c, max_width, max_height)

        self.img_3c = img_3c
        self.image_path = file_path
        self.initial_image = np.copy(self.img_3c)
        pixmap = np2pixmap(self.img_3c)

        H, W, _ = self.img_3c.shape
        H, W, _ = self.img_3c.shape

        if hasattr(self, "scene"):
            self.view.setScene(None)
            del self.scene

        self.scene = QGraphicsScene(0, 0, W, H)
        self.scene2 = QGraphicsScene(0, 0, W, H)
        self.end_point = None
        self.rect = None
        self.bg_img1 = self.scene.addPixmap(pixmap)
        self.bg_img2 = self.scene2.addPixmap(pixmap)
        self.bg_img1.setPos(0, 0)
        self.bg_img2.setPos(0, 0)
        self.view1.setScene(self.scene)  # 在第一个视图中显示图像
        self.view2.setScene(self.scene2)  # 在第二个视图中显示相同的图像
        # self.view2.setScene(self.initial_image)

        self.scene.mousePressEvent = self.mouse_press
        self.scene.mouseMoveEvent = self.mouse_move
        self.scene.mouseReleaseEvent = self.mouse_release

        # self.scene2.mousePressEvent = self.mouse_press
        # self.scene2.mouseMoveEvent = self.mouse_move
        # self.scene2.mouseReleaseEvent = self.mouse_release


    def resize_image(self, img, max_width, max_height):
        img_height, img_width, _ = img.shape
        if img_width > max_width or img_height > max_height:
            scale_x = max_width / img_width
            scale_y = max_height / img_height
            scale = min(scale_x, scale_y)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            img = Image.fromarray(img)
            img = img.resize((new_width, new_height), Image.ANTIALIAS)
            img = np.array(img)

        return img


    def mouse_press(self, ev):
        x, y = ev.scenePos().x(), ev.scenePos().y()
        if self.mode == "draw":
            self.is_mouse_down = True
            self.start_pos = ev.scenePos().x(), ev.scenePos().y()
            self.start_point = self.scene.addEllipse(
                x - self.half_point_size,
                y - self.half_point_size,
                self.point_size,
                self.point_size,
                pen=QPen(QColor("red")),
                brush=QBrush(QColor("red")),
            )

            self.coordinate_history.append((x, y))
            self.history.append(np.copy(self.img_3c))
        if self.mode == "difference":
            self.is_mouse_down = True
            self.start_pos = ev.scenePos().x(), ev.scenePos().y()
            self.start_point = self.scene.addEllipse(
                x - self.half_point_size,
                y - self.half_point_size,
                self.point_size,
                self.point_size,
                pen=QPen(QColor("yellow")),
                brush=QBrush(QColor("yellow")),
            )

            self.coordinate_history.append((x, y))
            self.history.append(np.copy(self.img_3c))

        elif self.mode == "restore":
            self.is_mouse_down = True
            self.start_pos = ev.scenePos().x(), ev.scenePos().y()
            self.start_point = self.scene.addEllipse(
                x - self.half_point_size,
                y - self.half_point_size,
                self.point_size,
                self.point_size,
                pen=QPen(QColor("green")),
                brush=QBrush(QColor("green")),
            )

            self.restore_state = np.copy(self.img_3c)
        elif self.mode == "describe":
            try:
                self.is_mouse_down = True
                self.drawing = True
                self.points = [ev.scenePos()]
                self.tag = 0

            except Exception as e:
                print(e)
        elif self.mode == "delete":
            self.is_mouse_down = True
            self.deleteing = True
            self.points = [ev.scenePos()]
            self.tag = 0

    def mouse_move(self, ev):
        if not self.is_mouse_down:
            return
        if self.mode!="describe" and self.mode!="delete":
            x, y = ev.scenePos().x(), ev.scenePos().y()

            if self.rect is not None:
                self.scene.removeItem(self.rect)
            sx, sy = self.start_pos
            xmin = int(min(x, sx))
            xmax = int(max(x, sx))
            ymin = int(min(y, sy))
            ymax = int(max(y, sy))


            if self.mode == "draw":
                self.rect = self.scene.addRect(
                    xmin, ymin, xmax - xmin, ymax - ymin, pen=QPen(QColor("red"))
                )
            if self.mode == "difference":
                self.rect = self.scene.addRect(
                    xmin, ymin, xmax - xmin, ymax - ymin, pen=QPen(QColor("yellow"))
                )
            elif self.mode == "restore":
                self.rect = self.scene.addRect(
                    xmin, ymin, xmax - xmin, ymax - ymin, pen=QPen(QColor("green"))
                )
        else:
            if self.mode == "describe" and self.drawing:


                try:
                    #print(self.points)


                    current_point = ev.scenePos()
                    if len(self.points) > 0:
                        # 使用QPainter进行绘制
                        if self.tag==0:
                            self.pixmap = np2pixmap(self.img_3c)
                            self.update_image()
                            self.tag=1
                        painter = QPainter(self.pixmap)
                        pen = QPen(QColor(0, 255, 0))
                        pen.setWidth(self.line_width)
                        painter.setPen(pen)
                        painter.drawLine(self.points[-1], current_point)
                        painter.end()
                        if self.bg_img is not None:
                            self.scene.removeItem(self.bg_img)
                        self.bg_img = self.scene.addPixmap(self.pixmap)

                        self.points.append(current_point)

                        #self.bg_img.setPos(0, 0)


                except Exception as e:
                    print(e)

            elif self.mode == "delete" and self.deleteing:

                try:
                    # print(self.points)

                    current_point = ev.scenePos()
                    if len(self.points) > 0:
                        # 使用QPainter进行绘制
                        if self.tag == 0:
                            self.pixmap = np2pixmap(self.img_3c)
                            self.update_image()
                            self.tag = 1
                        painter = QPainter(self.pixmap)
                        pen = QPen(QColor(0, 255, 0))
                        pen.setWidth(self.line_width)
                        painter.setPen(pen)
                        painter.drawLine(self.points[-1], current_point)
                        painter.end()
                        if self.bg_img is not None:
                            self.scene.removeItem(self.bg_img)
                        self.bg_img = self.scene.addPixmap(self.pixmap)

                        self.points.append(current_point)

                        # self.bg_img.setPos(0, 0)


                except Exception as e:
                    print(e)


    def update_image(self):
        pixmap = np2pixmap(self.img_3c)
        self.scene.removeItem(self.bg_img)
        self.bg_img = self.scene.addPixmap(pixmap)
        self.bg_img.setPos(0, 0)

    def mouse_release(self, ev):
        self.is_mouse_down = False
        if self.mode == "draw":
            color = colors[self.color_idx]
            self.mask_c[int(min(self.start_pos[1], ev.scenePos().y())):int(max(self.start_pos[1], ev.scenePos().y())),
                        int(min(self.start_pos[0], ev.scenePos().x())):int(max(self.start_pos[0], ev.scenePos().x()))] = color
            self.color_idx = (self.color_idx + 1) % len(colors)

            # time.sleep(1)

            xmin = int(min(self.start_pos[0], ev.scenePos().x()))
            xmax = int(max(self.start_pos[0], ev.scenePos().x()))
            ymin = int(min(self.start_pos[1], ev.scenePos().y()))
            ymax = int(max(self.start_pos[1], ev.scenePos().y()))

            region_to_render_white = self.initial_image[ymin:ymax, xmin:xmax]
            if region_to_render_white.shape[0] > 600  and region_to_render_white.shape[1] > 600:
                print(region_to_render_white.shape)
                image = Image.fromarray(region_to_render_white)
                segmented_image = unet_instance1.detect_image(image)
                image_array = np.array(segmented_image)
                self.img_3c[ymin:ymax, xmin:xmax] = image_array
            else:
                print(region_to_render_white.shape)
                image = Image.fromarray(region_to_render_white)
                segmented_image = unet_instance.detect_image(image)
                image_array = np.array(segmented_image)
                self.img_3c[ymin:ymax, xmin:xmax] = image_array
            self.update_image()


        if self.mode == "difference":
            xmin = int(min(self.start_pos[0], ev.scenePos().x()))
            xmax = int(max(self.start_pos[0], ev.scenePos().x()))
            ymin = int(min(self.start_pos[1], ev.scenePos().y()))
            ymax = int(max(self.start_pos[1], ev.scenePos().y()))
            self.show_difference_percentage(xmin, xmax, ymin, ymax)


        elif self.mode == "restore":
            xmin = int(min(self.start_pos[0], ev.scenePos().x()))
            xmax = int(max(self.start_pos[0], ev.scenePos().x()))
            ymin = int(min(self.start_pos[1], ev.scenePos().y()))
            ymax = int(max(self.start_pos[1], ev.scenePos().y()))

            region_to_restore = self.initial_image[ymin:ymax, xmin:xmax]

            # time.sleep(1)

            self.img_3c[ymin:ymax, xmin:xmax] = region_to_restore
            self.update_image()

        elif self.mode == "describe" and self.drawing:
            try:
                self.drawing = False
                self.tag = 0
                if len(self.points) >= 3:
                    start_point = self.points[0]
                    end_point = self.points[-1]

                self.drawEdge(start_point, end_point)
                self.fillMask()
                self.applyMask()
                # self.update_image()
            except Exception as e:
                print(e)
        elif self.mode == "delete" and self.deleteing:
            try:
                self.deleteing = False
                self.tag = 0
                # print(self.points)
                if len(self.points) >= 3:
                    start_point = self.points[0]
                    end_point = self.points[-1]

                self.drawEdge(start_point, end_point)

                self.deleteMask()
            except Exception as e:
                print(e)

    def undo_last_edit(self):
        if self.history:
            self.img_3c = self.history.pop()
            self.update_image()

    def view_history(self):
        if self.coordinate_history:
            coordinate_history_text = "\n".join([f"({x}, {y})" for x, y in self.coordinate_history])
            QMessageBox.information(self, "坐标历史记录", coordinate_history_text)
        else:
            QMessageBox.information(self, "坐标历史记录", "无可用历史记录.")

    def save_mask(self):
        out_path = f"{self.image_path.split('.')[0]}_mask.jpg"
        io.imsave(out_path, self.img_3c)
        # # 确保图像具有相同的尺寸
        # if image1.shape != image2.shape:
        #     image1 = cv2.resize(image1, (image2.shape[1], image2.shape[0]))

    def show_difference_percentage(self, xmin, xmax, ymin, ymax):
        region_to_compare = self.initial_image[ymin:ymax, xmin:xmax]
        region_to_render = self.img_3c[ymin:ymax, xmin:xmax]

        diff_percentage = 1 - ((region_to_compare == region_to_render).sum() / region_to_compare.size)

        # 创建弹窗来显示百分比和区域
        region_info = f"Region:\n{region_to_render}"
        message = f"Difference Percentage: {diff_percentage:.2%}"
        QMessageBox.information(self, "Difference Percentage", message)

    def toggle_mode(self):
        if self.mode == "draw":
            self.mode = "restore"
        else:
            self.mode = "draw"
            self.restore_region_history.clear()

    def toggle_edge_mode(self):
        self.mode = "describe"
        self.drawing = False
        self.points = []

    def delete_edge(self):
        self.mode = "delete"
        self.deleteing = True
        self.points = []

    def fillMask(self):
        if self.img_3c is not None:
            height, width, _ = self.img_3c.shape
            self.mask = np.zeros((height, width, 4), dtype=np.uint8)  # 4通道图像

            points_array = np.array(
                [(point.x(), point.y()) for point in self.points], dtype=np.int32
            )
            # for point in self.points:
            #     print(self.img_3c[int(point.x()), int(point.y())])

            cv2.fillPoly(self.mask, [points_array], (128, 0, 0, 50))

    def deleteMask(self):
        if self.img_3c is not None:
            height, width, _ = self.img_3c.shape
            points_array = np.array(
                [(point.x(), point.y()) for point in self.points], dtype=np.int32
            )

            mask = np.zeros((height, width), dtype=np.uint8)
            cv2.fillPoly(mask, [points_array], 1)

            # 3. 使用遮罩提取多边形区域
            extracted_region = cv2.bitwise_and(self.initial_image, self.initial_image, mask=mask)

            # 4. 将提取的区域替换为要填充的内容
            result_image = self.img_3c.copy()  # 创建目标图像的副本
            result_image[mask == 1] = extracted_region[mask == 1]

            self.img_3c = result_image
            self.update_image()

    def applyMask(self):
        if self.img_3c is not None and self.mask is not None:
            mask_inv = cv2.bitwise_not(self.mask[:, :, 3])
            img_bg = cv2.bitwise_and(self.img_3c, self.img_3c, mask=mask_inv)

            img_fg = self.mask[:, :, :3]

            result = cv2.add(img_bg, img_fg)
            self.img_3c = result
            self.update_image()




    def restore_mode(self):
            self.mode = "restore"
    def draw_mode(self):
            self.mode = "draw"

    def difference_mode(self):
        self.mode = "difference"

    def drawEdge(self, point1, point2):

        if len(self.points) >= 2:
            for i in range(len(self.points) - 1):
                pen = QPen(QColor(0, 255, 0))
                pen.setWidth(self.line_width)
                self.scene.addLine(point1.x(), point1.y(), point2.x(), point2.y(), pen)


app = QApplication(sys.argv)
app.setWindowIcon(QIcon('img/11.png'))  # 设置应用程序图标
app.setApplicationName("徐州第一人民医院")  # 设置应用程序名称
w = Window()
w.show()
sys.exit(app.exec_())