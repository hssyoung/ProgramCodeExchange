"""
ProgramCode Converter

Author: Yangshengquan
License: MIT License
Copyright (c) 2023 yangsq1026@gmain.com

This software is provided "as is", without any warranty expressed or implied.
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QTreeWidget,
    QTreeWidgetItem,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QAction,
    QMenu,
    QComboBox,
    QLabel,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import chardet
from openai import OpenAI
import re
from pathlib import Path


def read_file_with_encoding_detection(file_path):
    """
    检测文件编码并以文本方式读取文件内容。

    参数:
    file_path: str - 文件的路径

    返回:
    content: str - 文件的内容
    encoding: str - 检测到的编码
    confidence: float - 检测到编码的可信度
    """
    try:
        # 读取文件的前1024个字节来检测编码
        with open(file_path, "rb") as f:
            raw_data = f.read(1024)  # 读取前1024个字节以检测编码
            result = chardet.detect(raw_data)
            encoding = result["encoding"]
            confidence = result["confidence"]
            print(f"检测到编码: {encoding}，可信度: {confidence}")

        # 使用检测到的编码读取文件
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()  # 读取文件内容
        return content, encoding, confidence
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
    except IOError as e:
        print(f"读取文件时发生错误: {e}")
    except UnicodeDecodeError:
        print(f"文件编码错误: {file_path}")
        # 尝试使用 utf-8 编码读取
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()  # 读取文件内容
        return content, "utf-8", 1.0  # 假设使用 utf-8 时可信度为 1.0
    return None, None, None  # 返回空值以表示发生了错误


client = OpenAI(
    base_url="https://api.xxxxxxx.org",
    api_key="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
)


class Worker(QThread):
    log_signal = pyqtSignal(str)  # 创建信号以发送日志信息
    refresh_tree_signal = pyqtSignal(QTreeWidget)  # 定义信号，传递 QTreeWidget
    finished_signal = pyqtSignal()  # 添加完成信号

    def __init__(self,file_list, folder_path, additional_input):
        super().__init__()
        self.file_list = file_list
        if folder_path != "":
            self.folder_path = os.path.abspath(folder_path)
        else:
            self.folder_path = ""

        self.additional_input = additional_input
        self.log_signal.emit(f"读取文件1: {self.folder_path}")
        self.language = ""
        self._stop_thread = False
        self.is_running = False  # 添加任务状态标志

    def set_language(self, language):
        self.language = language  # 接收并存储语言

    def set_newpath(self, left_path, right_path):
        self.leftpath = left_path
        self.rightpath = right_path     #  = language  # 接收并存储语言
    """ 
                fileItems = os.listdir(self.folder_path)
                for file_name in fileItems:
                    self.log_signal.emit(f"读取文件: {file_name}")
                    if self._stop_thread:  # 检查是否停止
                        break
                    full_file_path = os.path.join(self.folder_path, file_name)
                    if os.path.isfile(full_file_path):  # 仅处理文件
                        #self.log_signal.emit(f"读取文件: {full_file_path}")
                        content, encoding, confidence = read_file_with_encoding_detection(
                            full_file_path
                        )
                        if content is not None:
                            self.getOpenAiResponse(content)
                        elif self.additional_input != "":
                            self.getOpenAiResponse(addtionText) """
    def run(self):
        # 遍历文件夹并读取文件内容
        self.is_running = True  # 添加任务状态标志
        try:        
            addtionText = self.additional_input
            self.log_signal.emit(f"读取文件: {self.folder_path},{addtionText},size:{len(self.file_list)}")    
            if len(self.file_list) == 0:
                self.getOpenAiResponse(addtionText)
            else:    
                for file_path in self.file_list:
                    if self._stop_thread:
                        break
                    if os.path.isfile(file_path):
                        self.log_signal.emit(f"正在读取文件: {file_path},{addtionText}")
                        content, encoding, confidence = read_file_with_encoding_detection(
                            file_path
                        )
                        self.log_signal.emit(f"文件编码: {encoding}, 置信度: {confidence}")
                        if content is not None:
                            self.getOpenAiResponse(content+addtionText,file_path)
                        elif addtionText != "":
                            self.getOpenAiResponse(addtionText,file_path)
                        else:
                            return

        except Exception as e:
            self.log_signal.emit(f"处理文件夹时发生错误: {str(e)}")
        finally:
            self.is_running = False  # 重置任务状态
            self.finished_signal.emit()  # 发出完成信号
    def stop(self):
        self._stop_thread = True  # 设置停止标志
    def read_file_content(self, file_path):
        # 读取文件内容并发送到日志
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.log_signal.emit(f"文件内容: {content}")
        except Exception as e:
            self.log_signal.emit(f"无法读取文件内容: {file_path}, 错误: {str(e)}")

    def get_file_extension(self,content, language):
        extaname = ""
        # 设置一个字典来映射语言与其可能的后缀
        language_extensions = {
            "转成 C++": (["cpp", "h"], ".cpp", ".h"),
            "转成 JAVA": (["java"], ".java"),
            "转成 Python": (["py"], ".py"),
            "转成 Rust": (["rust"], ".rs"),
            "转成 C#": (["csharp"], ".cs"),
            "转成 Go": (["go"], ".go"),
            "转成 C": (["c"], ".c"),
            "转成 JavaScript": (["javascript"], "js"),
            "None": ([None], None),
        }

        if language in language_extensions:
            extensions, primary_ext, fallback_ext = language_extensions[language]

            for ext in extensions:
                index = content.find(ext)
                if index != -1:
                    extaname = primary_ext if primary_ext else fallback_ext
                    break
        #self.log_signal.emit(f"get_file_extension:{content}:{extaname}");        
        return extaname

    def write_file_content(self, content, file_path):
        # 将内容写入文件
        try:
            prefix = content[:5]

            extaname = self.get_file_extension(prefix, self.language)
            if extaname == "":
                self.log_signal.emit("未找到有效的扩展名，无法写入文件.")
                return

            if self.rightpath == "":
                self.log_signal.emit("右边路径为空，无法写入文件.")
                return
            lfpath = os.path.normpath(self.leftpath)
            rfpath = os.path.normpath(self.rightpath)
            index = file_path.find(lfpath)
            self.log_signal.emit(f"---{self.file_path}------find: {index}")
            if index != -1:
                if index == 0:
                    remaining_path = file_path[len(lfpath):]
                else:
                    remaining_path = file_path[index:]
                
                new_file_path = rfpath + remaining_path              
                new_file_path = os.path.normpath(new_file_path)  # 规范化路径
            
                #self.log_signal.emit(f"新文件路径: {new_file_path},rp={rfpath},ext:{ remaining_path}")
                base_name = os.path.basename(new_file_path).split(".")[0]
                new_file_path = os.path.join(
                    os.path.dirname(new_file_path), base_name + extaname
                )  # 添加新的扩展名
                #self.log_signal.emit(f"新文件路径: {new_file_path}")

                with open(new_file_path, "w", encoding="utf-8") as f:  # 使用 "w" 模式写入文件
                    f.write(content)
                    self.log_signal.emit(f"已成功写入文件: {new_file_path}")                   
                    self.refresh_tree_signal.emit()  # 发出信号，刷新树形控件
            else:
                self.log_signal.emit("左边路径未找到，无法执行替换操作.")
                return

            

        except Exception as e:
            self.log_signal.emit(f"无法写入文件: {file_path}, 错误: {str(e)}")



    def stop(self):
        self._stop_thread = True  # 设置停止标志

    def split_text(self,text, max_length=4096):
        """
        将文本分割成多个部分，每个部分的长度不超过max_length字节。

        参数:
        text: str - 要分割的文本
        max_length: int - 每个部分的最大长度

        返回:
        List[str] - 分割后的文本列表
        """
        parts = []
        while len(text) > max_length:
            split_index = text.rfind(' ', 0, max_length)
            if split_index == -1:
                split_index = max_length  # 如果没有找到空格，则强制分割
            parts.append(text[:split_index])
            text = text[split_index:].strip()
        parts.append(text)
        return parts

    def send_request_to_openai(self,prompt):
        """
        向OpenAI API发送请求并返回响应。

        参数:
        prompt: str - 提示文本

        返回:
        str - API响应
        """
        response = client.chat.completions.create(
            messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="gpt-3.5-turbo",
        )
        resulttext = response.choices[0].message.content       
        return resulttext
    def process_large_text(self,text):
        """
        处理大文本，将其分割成多个部分，逐个发送请求，并合并响应。

        参数:
        text: str - 要处理的大文本

        返回:
        str - 合并后的响应
        """
        parts = self.split_text(text)
        responses = []
        for part in parts:
            response = self.send_request_to_openai(part)
            responses.append(response)
        return '\n'.join(responses)
    def getOpenAiResponse(self, content,file_path):
        response_content = self.process_large_text(content)
     # 使用正则表达式提取应答代码部分
        code_pattern = re.compile(r"```(.*?)```", re.DOTALL)
        code_matches = code_pattern.findall(response_content)
        # 输出提取的代码部分
        self.log_signal.emit(f"~~~~~~~~~~~~~~~~~~~~~~\n{response_content}\n~~~~~~~~~~~~~~~~~~~~~~")
        if code_matches:
            for index, code in enumerate(code_matches):
                #self.log_signal.emit(f"提取的代码部分 {index + 1}:")
                #self.log_signal.emit(f"\n{code.strip()}\n")
                self.write_file_content(file_path, code.strip())
        #else:
        #    self.log_signal.emit(f"\n{response_content}\n")

    def getOpenAiResponseEx(self, content, additional_input, max_length=4000):
        self.content = content
        self.additional_input = additional_input

        # 合并内容
        full_input = self.content + self.additional_input
        self.log_signal.emit(f"正在进行中...")

        # 分割输入为多个部分以避免超过API限制
        input_parts = self.split_text(full_input, max_length=max_length)
        self.log_signal.emit(f"ysq ask:\n {input_parts}")
        for part in input_parts:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": part,
                    }
                ],
                model="gpt-3.5-turbo",
            )
            #self.log_signal.emit(f"输入: {part}")
            if chat_completion.choices:
                # 使用属性访问内容
                response_content = chat_completion.choices[0].message.content

                # 使用正则表达式提取应答代码部分
                code_pattern = re.compile(r"```(.*?)```", re.DOTALL)
                code_matches = code_pattern.findall(response_content)
                # 输出提取的代码部分
                if code_matches:
                    for index, code in enumerate(code_matches):
                        self.log_signal.emit(f"提取的代码部分 {index + 1}:")
                        self.log_signal.emit(f"\n{code.strip()}")
                        self.write_file_content(self.folder_path, code.strip())
                else:
                    self.log_signal.emit(f"\n{response_content}")
            else:
                response_contenterr = "没有得到有效的回复。"
                self.log_signal.emit(f"\n{response_contenterr}")

        self.log_signal.emit(f"问答结束.")

class LogTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super(LogTextEdit, self).__init__(parent)

    def contextMenuEvent(self, event):
        # 创建上下文菜单
        context_menu = QMenu(self)

        # 添加“复制”菜单项
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        context_menu.addAction(copy_action)

        # 添加“清空”菜单项
        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self.clear_log)
        context_menu.addAction(clear_action)

        # 显示菜单
        context_menu.exec_(event.globalPos())

    def copy_to_clipboard(self):
        text = self.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "提示", "日志内容已复制到剪贴板。")

    def clear_log(self):
        self.clear()
        QMessageBox.information(self, "提示", "日志内容已清空。")


class FileTreeWidget(QWidget):
    refresh_tree_signal = pyqtSignal(QTreeWidget)  # 定义信号，传递 QTreeWidget
    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread = None  # 管理线程的状态

    def initUI(self):
        self.main_layout = QVBoxLayout()  # 主布局
        self.setWindowTitle("语言转换器")

        # 设置布局
        self.left_layout = QVBoxLayout()  # QHBoxLayout #

        # 添加标签以显示所选的选项
        self.label = QLabel("请选择要转换的语言:")
        # 创建下拉框
        self.language_combo = QComboBox()
        self.language_combo.addItems(
            [
                "None",
                "转成 C++",
                "转成 JAVA",
                "转成 Python",
                "转成 Rust",
                "转成 C#",
                "转成 Go",
                "转成 C",
                "转成 JavaScript",
            ]
        )
        self.language_combo.currentIndexChanged.connect(self.update_language_option)

        self.left_layout.addWidget(self.label)
        self.left_layout.addWidget(self.language_combo)
        # 动态添加的编辑框
        self.dynamic_input = QLineEdit()
        self.dynamic_input.setPlaceholderText("在这里输入额外信息...")
        self.left_layout.addWidget(self.dynamic_input)  # 添加到布局，但默认可见

        self.send_button = QPushButton("发送")
        # 创建一个 QWidget 作为左侧布局的容器
        left_widget = QWidget()
        left_widget.setLayout(
            self.left_layout
        )  # 将 left_layout 设置为该 QWidget 的布局

        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(left_widget)
        self.top_layout.addWidget(self.send_button)

        self.main_layout.addLayout(self.top_layout)  # 添加到主布局上方
        # 将控件添加到布局中
        # self.layout.addWidget(self.label)
        # self.layout.addWidget(self.language_combo)

        # self.setLayout(self.layout)
        # 上方输入框和发送按钮
        # self.send_input = QLineEdit()

        # self.top_layout = QHBoxLayout()  # 上方布局
        # self.top_layout.addWidget(self.send_input)

        # self.main_layout.addWidget(self.label)
        # self.main_layout.addWidget(self.language_combo)

        # 左右树形布局
        self.left_layout = QVBoxLayout()
        self.left_tree = QTreeWidget()
        self.left_tree.setHeaderLabels(["Files"])

        # 左侧输入框和浏览按钮
        self.left_input = QLineEdit()
        self.left_browse_button = QPushButton("浏览")
        self.left_browse_button.clicked.connect(
            lambda: self.load_directory(self.left_input, self.left_tree)
        )
        self.send_button.clicked.connect(
            lambda: self.send_message(self.dynamic_input, self.left_input)
        )

        self.left_layout.addWidget(self.left_input)
        self.left_layout.addWidget(self.left_browse_button)
        self.left_layout.addWidget(self.left_tree)

        self.right_layout = QVBoxLayout()
        self.right_tree = QTreeWidget()
        self.right_tree.setHeaderLabels(["Files"])

        # 右侧输入框和浏览按钮
        self.right_input = QLineEdit()
        self.right_browse_button = QPushButton("浏览")
        self.right_browse_button.clicked.connect(
            lambda: self.load_directory(self.right_input, self.right_tree)
        )

        self.right_layout.addWidget(self.right_input)
        self.right_layout.addWidget(self.right_browse_button)
        self.right_layout.addWidget(self.right_tree)
        # 连接信号以检测复选框状态改变
        self.left_tree.itemChanged.connect(self.on_item_changed)
        self.right_tree.itemChanged.connect(self.on_item_changed)

        # 将左右布局水平放置
        self.horizontal_layout = QHBoxLayout()
        self.horizontal_layout.addLayout(self.left_layout)
        self.horizontal_layout.addLayout(self.right_layout)

        self.main_layout.addLayout(self.horizontal_layout)  # 添加左右布局到主布局

        # 日志文本框
        self.log_box = LogTextEdit()
        self.log_box.setReadOnly(True)  # 设置为只读
        self.main_layout.addWidget(self.log_box)  # 添加到主布局的底部

        self.setLayout(self.main_layout)

    def load_directory(self, line_edit, tree):
        folder_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if folder_path:
            line_edit.setText(folder_path)  # 设置输入框文本
            self.populate_tree(tree, folder_path)

    def populate_tree(self, tree, path):
        tree.clear()  # 清空树形控件
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            tree_item = QTreeWidgetItem(tree, [item])
            tree_item.setCheckState(0, Qt.Unchecked)
            if os.path.isdir(full_path):
                self.add_items(tree_item, full_path)

    def add_items(self, tree_item, path):
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            child_item = QTreeWidgetItem(tree_item, [item])
            child_item.setCheckState(0, Qt.Unchecked)
            if os.path.isdir(full_path):
                self.add_items(child_item, full_path)  # 递归添加子目录
    def refresh_tree(self):   
        self.populate_tree(self.right_tree, self.right_input.text())  # 刷新树形控件tree.currentItem().text(0)
    def update_language_option(self, index):
        self.language_option = self.language_combo.itemText(index)  # 更新选中的语言
        dirpath = self.left_input.text() + "/" + self.language_option
        self.log_box.append(f"正在创建文件夹: {dirpath}")
        self.create_folder(dirpath)
        self.right_input.setText(dirpath)

    def create_folder(self, folder_path):
        try:
            # Path.mkdir() 创建文件夹
            path = Path(folder_path)
            path.mkdir(parents=True, exist_ok=True)
            print(f"文件夹已创建: {folder_path}")
        except Exception as e:
            print(f"创建文件夹时出错: {str(e)}")
    def get_checked_files(self, parent_item, base_path):
        checked_files = []
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            #self.log_box.append(f"处理项: {child_item.text(0)}")  # 调试信息
            
            full_path = os.path.join(base_path, child_item.text(0))
           # self.log_box.append(f"选中项: {full_path}")  # 调试信息
            if os.path.isfile(full_path) and child_item.checkState(0) == Qt.Checked:
                checked_files.append(full_path)
            elif os.path.isdir(full_path):
                # 递归处理子项
                #self.log_box.append(f"递归进入子目录: {full_path}")  # 调试信息
                checked_files.extend(self.get_checked_files(child_item, full_path))
        return checked_files
    def send_messageEx(self, send_input, line_leftinput):
        # 如果当前线程还在运行，提示用户
        if self.thread is not None and self.thread.isRunning():
            self.log_box.append("已有任务正在运行，请稍后...")
            return

        checked_count = 0  # 初始化勾选项计数
        #self.log_box.append(f"send_message...{self.left_tree.topLevelItemCount()}")
        for index in range(self.left_tree.topLevelItemCount()):
            item = self.left_tree.topLevelItem(index)
            checked_count += self.get_checked_items(item)

        addtionText = send_input.text()
        #self.log_box.append(f"我:{checked_count}, {addtionText}")
        if self.language_combo.currentText() != "None":
            addtionText = self.language_combo.currentText() + addtionText
        if checked_count > 0:
            for index in range(self.left_tree.topLevelItemCount()):
                item = self.left_tree.topLevelItem(index)
                #self.log_box.append(f"正在处理文件夹...{item.text(0)}")
                if item.checkState(0) == Qt.Checked:  # 检查勾选状态
                    edit_path = line_leftinput.text() + "/"
                    folder_path = edit_path + self.get_full_path(item)
                    if os.path.isdir(folder_path):  # 确保是有效的文件夹路径
                        self.log_box.append(f"正在处理文件夹: {folder_path}")

                    # 调用工作线程
                    self.thread = Worker(folder_path, addtionText)
                    self.thread.log_signal.connect(self.log_message)  # 连接信号
                    self.thread.set_language(
                        self.language_combo.currentText()
                    )  # 将选中的语言传递给线程
                    self.thread.set_newpath(self.left_input.text(), self.right_input.text())  # 设置新路径
                    self.thread.refresh_tree_signal.connect(self.refresh_tree)  # 连接信号到槽函数
                    self.thread.start()  # 启动线程
        elif addtionText != "":
            # 调用工作线程
            self.thread = Worker("", addtionText)
            self.thread.log_signal.connect(self.log_message)  # 连接信号
            self.thread.start()  # 启动线程
    def send_message(self, send_input, line_leftinput):
        # 如果当前线程还在运行，提示用户
        if self.thread is not None and self.thread.isRunning():
            self.log_box.append("已有任务正在运行，请稍后...")
            return
        edit_path = line_leftinput.text() + "/"
        folder_path = edit_path
        checked_files = self.get_checked_files(self.left_tree.invisibleRootItem(), folder_path)
        
        addtionText = send_input.text()
        
        if self.language_combo.currentText() != "None":
            addtionText = self.language_combo.currentText() + addtionText
        
        if len(checked_files) == 0 and addtionText == "":
            self.log_box.append("请选择文件或输入内容")
            return
            # 调用工作线程
        self.thread = Worker(checked_files,folder_path, addtionText)
        self.thread.log_signal.connect(self.log_message)  # 连接信号
        self.thread.set_language(
                        self.language_combo.currentText()
                    )  # 将选中的语言传递给线程
        self.thread.set_newpath(self.left_input.text(), self.right_input.text())  # 设置新路径
        self.thread.refresh_tree_signal.connect(self.refresh_tree)  # 连接信号到槽函数
        self.thread.start()  # 启动线程

    def get_checked_items(self, item):
        """递归计算当前项及其子项的勾选状态"""
        count = 0
        if item.checkState(0) == Qt.Checked:
            count += 1
        for i in range(item.childCount()):
            child_item = item.child(i)
            count += self.get_checked_items(child_item)
        return count

    def get_full_path(self, item):
        """获取选中项的完整路径"""
        path = []
        while item:
            path.append(item.text(0))
            item = item.parent()
        return os.path.join(*reversed(path))

    def log_message(self, message):
        """更新日志框"""
        self.log_box.append(message)

    def on_thread_finished(self):
        """处理线程完成信号"""
        self.log_box.append("文件处理完成!")

    def on_item_changed(self, item, column):
        """处理勾选状态变化"""
        if item.checkState(0) == Qt.Checked:
            # 勾选时勾选所有子项
            self.set_checked_recursively(item, Qt.Checked)
        else:
            # 取消勾选时取消所有子项
            self.set_checked_recursively(item, Qt.Unchecked)

    def set_checked_recursivelyEx(self, item, state):
        """递归设置当前项及其子项的勾选状态"""
        item.setCheckState(0, state)  # 设置当前项的勾选状态
        for i in range(item.childCount()):
            child_item = item.child(i)
            self.set_checked_recursively(child_item, state)  # 递归设置子项状态
    def set_checked_recursively(self, parent_item, state, selected_child_index=None):
        """递归设置当前项及其子项的勾选状态"""
        
        # 设置当前项的勾选状态
        parent_item.setCheckState(0, state)  # 设置当前项的勾选状态

        # 如果没有指定子项索引，则设置所有子项
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            if selected_child_index is not None and i == selected_child_index:
                # 只选中指定的子项
                child_item.setCheckState(0, Qt.Checked)
            else:
                # 取消勾选未选中的子项
                child_item.setCheckState(0, Qt.Unchecked)

        # 如果有需要递归设置的条件
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            if selected_child_index is None or i == selected_child_index:
                self.set_checked_recursively(child_item, state)  # 递归设置已选中的子项状态


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileTreeWidget()
    window.setWindowTitle("开发语言转化工具,code by yangsq1026@gmail.com")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
