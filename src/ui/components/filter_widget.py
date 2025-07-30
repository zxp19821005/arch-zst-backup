# -*- coding: utf-8 -*-
"""过滤器组件"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QCheckBox, QDateEdit, QGroupBox
)
from PySide6.QtCore import Qt, Signal, QDate
from datetime import datetime, timedelta

class FilterWidget(QWidget):
    """高级过滤器组件"""
    
    # 定义信号
    filter_changed = Signal(dict)  # 过滤条件变化信号
    
    def __init__(self, filter_config, parent=None):
        """
        初始化过滤器组件
        :param filter_config: 过滤器配置字典
        :param parent: 父组件
        """
        super().__init__(parent)
        
        self.filter_config = filter_config
        self.filter_widgets = {}
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 过滤器组
        filter_group = QGroupBox("过滤条件")
        filter_layout = QVBoxLayout(filter_group)
        
        # 创建过滤器控件
        for filter_name, config in self.filter_config.items():
            filter_widget = self.create_filter_widget(filter_name, config)
            if filter_widget:
                filter_layout.addWidget(filter_widget)
        
        layout.addWidget(filter_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("应用过滤")
        apply_btn.clicked.connect(self.apply_filter)
        button_layout.addWidget(apply_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_filter)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def create_filter_widget(self, filter_name, config):
        """创建单个过滤器控件"""
        filter_type = config.get('type', 'text')
        display_name = config.get('display_name', filter_name)
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # 标签
        label = QLabel(f"{display_name}:")
        label.setMinimumWidth(80)
        layout.addWidget(label)
        
        # 根据类型创建控件
        if filter_type == 'text':
            control = QLineEdit()
            control.setPlaceholderText(config.get('placeholder', ''))
            control.textChanged.connect(self.on_filter_changed)
            
        elif filter_type == 'combo':
            control = QComboBox()
            options = config.get('options', [])
            control.addItem("全部", "")
            for option in options:
                if isinstance(option, dict):
                    control.addItem(option['label'], option['value'])
                else:
                    control.addItem(str(option), option)
            control.currentTextChanged.connect(self.on_filter_changed)
            
        elif filter_type == 'date_range':
            # 日期范围控件
            date_widget = QWidget()
            date_layout = QHBoxLayout(date_widget)
            
            from_date = QDateEdit()
            from_date.setDate(QDate.currentDate().addDays(-30))
            from_date.setCalendarPopup(True)
            from_date.dateChanged.connect(self.on_filter_changed)
            
            to_date = QDateEdit()
            to_date.setDate(QDate.currentDate())
            to_date.setCalendarPopup(True)
            to_date.dateChanged.connect(self.on_filter_changed)
            
            date_layout.addWidget(QLabel("从:"))
            date_layout.addWidget(from_date)
            date_layout.addWidget(QLabel("到:"))
            date_layout.addWidget(to_date)
            
            control = date_widget
            self.filter_widgets[f"{filter_name}_from"] = from_date
            self.filter_widgets[f"{filter_name}_to"] = to_date
            
        elif filter_type == 'checkbox':
            control = QCheckBox(config.get('text', ''))
            control.stateChanged.connect(self.on_filter_changed)
            
        else:
            return None
        
        layout.addWidget(control)
        layout.addStretch()
        
        # 保存控件引用
        if filter_type != 'date_range':
            self.filter_widgets[filter_name] = control
        
        return widget
    
    def on_filter_changed(self):
        """过滤条件变化"""
        # 可以在这里添加实时过滤逻辑
        pass
    
    def apply_filter(self):
        """应用过滤条件"""
        filter_conditions = {}
        
        for filter_name, config in self.filter_config.items():
            filter_type = config.get('type', 'text')
            
            if filter_type == 'text':
                widget = self.filter_widgets.get(filter_name)
                if widget:
                    value = widget.text().strip()
                    if value:
                        filter_conditions[filter_name] = {'type': 'text', 'value': value}
            
            elif filter_type == 'combo':
                widget = self.filter_widgets.get(filter_name)
                if widget:
                    value = widget.currentData()
                    if value:
                        filter_conditions[filter_name] = {'type': 'combo', 'value': value}
            
            elif filter_type == 'date_range':
                from_widget = self.filter_widgets.get(f"{filter_name}_from")
                to_widget = self.filter_widgets.get(f"{filter_name}_to")
                if from_widget and to_widget:
                    from_date = from_widget.date().toPython()
                    to_date = to_widget.date().toPython()
                    filter_conditions[filter_name] = {
                        'type': 'date_range',
                        'from': from_date,
                        'to': to_date
                    }
            
            elif filter_type == 'checkbox':
                widget = self.filter_widgets.get(filter_name)
                if widget and widget.isChecked():
                    filter_conditions[filter_name] = {'type': 'checkbox', 'value': True}
        
        # 发出过滤信号
        self.filter_changed.emit(filter_conditions)
    
    def reset_filter(self):
        """重置过滤条件"""
        for filter_name, widget in self.filter_widgets.items():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)
            elif isinstance(widget, QDateEdit):
                if filter_name.endswith('_from'):
                    widget.setDate(QDate.currentDate().addDays(-30))
                else:
                    widget.setDate(QDate.currentDate())
        
        # 应用重置后的过滤
        self.apply_filter()
    
    def get_current_filters(self):
        """获取当前过滤条件"""
        self.apply_filter()
        return self.get_last_filter_conditions()
    
    def set_filter_value(self, filter_name, value):
        """设置过滤器值"""
        widget = self.filter_widgets.get(filter_name)
        if not widget:
            return
        
        if isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, QComboBox):
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QDateEdit):
            if isinstance(value, str):
                date = QDate.fromString(value, Qt.DateFormat.ISODate)
            else:
                date = QDate(value)
            widget.setDate(date)
