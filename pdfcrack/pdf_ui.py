#!/usr/bin/env python3
"""
PDF Password Cracker UI

A clean, Apple-style UI for batch processing password-protected PDF files.
"""

import sys
import os
from typing import List, Dict, Tuple, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout, QFileDialog, QWidget,
                             QProgressBar, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLineEdit, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent

# Import the PDF processing functions
from pdf_crack import analyze_pdf
from pdf_unlock import unlock_pdf


class PDFProcessingThread(QThread):
    """Thread for processing PDFs in the background"""
    progress_updated = pyqtSignal(int, int)  # current, total
    file_processed = pyqtSignal(str, bool, str)  # filename, success, message
    processing_finished = pyqtSignal()
    
    def __init__(self, files: List[str], output_dir: str, password: str, use_crack: bool):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.password = password
        self.use_crack = use_crack
        self.is_running = True
        
    def run(self):
        for i, input_file in enumerate(self.files):
            if not self.is_running:
                break
                
            filename = os.path.basename(input_file)
            output_file = os.path.join(self.output_dir, f"unlocked_{filename}")
            
            # Update progress
            self.progress_updated.emit(i + 1, len(self.files))
            
            # Process the file
            if self.use_crack and not self.password:
                # Try to crack the password
                password = analyze_pdf(input_file)
                if password is not None:
                    success, error = unlock_pdf(input_file, output_file, password)
                else:
                    success, error = False, "Unable to bypass PDF protection"
            else:
                # Use the provided password
                success, error = unlock_pdf(input_file, output_file, self.password)
                
            # Emit the result
            self.file_processed.emit(filename, success, error if not success else "")
            
        self.processing_finished.emit()
        
    def stop(self):
        self.is_running = False


class DropArea(QWidget):
    """Custom widget that accepts file drops"""
    files_dropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        layout = QVBoxLayout()
        
        self.label = QLabel("Drag & Drop PDF Files Here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        self.label.setFont(font)
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # Set minimum size
        self.setMinimumSize(400, 300)  # Increased height for better visibility
        
        # Set stylesheet
        self.setStyleSheet("""
            background-color: #f5f5f7;
            border: 2px dashed #86868b;
            border-radius: 10px;
            padding: 30px;  # Increased padding
        """)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                background-color: #e8e8ed;
                border: 2px dashed #0066cc;
                border-radius: 10px;
                padding: 20px;
            """)
            
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            background-color: #f5f5f7;
            border: 2px dashed #86868b;
            border-radius: 10px;
            padding: 20px;
        """)
        
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.pdf'):
                files.append(path)
                
        if files:
            self.files_dropped.emit(files)
            
        self.setStyleSheet("""
            background-color: #f5f5f7;
            border: 2px dashed #86868b;
            border-radius: 10px;
            padding: 20px;
        """)


class PDFCrackerUI(QMainWindow):
    """Main UI window for the PDF password cracker"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.pdf_files = []
        self.processing_thread = None
        self.output_directory = os.path.expanduser("~/Documents")
        
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("PDF Unlock Tool")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create drop area
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_files)
        main_layout.addWidget(self.drop_area)
        
        # Add spacing between drop area and buttons
        main_layout.addSpacing(40)  # Increased spacing
        
        # Create button layout with increased spacing
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)  # Add spacing between buttons
        
        # Adjust button sizes and styles
        self.select_files_btn = QPushButton("Select PDF Files")
        self.select_files_btn.clicked.connect(self.select_files)
        self.select_files_btn.setMinimumHeight(45)  # Increased button height
        self.select_files_btn.setMinimumWidth(180)  # Set minimum width
        self.select_files_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #0055b3;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        
        self.select_output_btn = QPushButton("Select Output Folder")
        self.select_output_btn.clicked.connect(self.select_output_directory)
        self.select_output_btn.setMinimumHeight(45)  # Increased button height
        self.select_output_btn.setMinimumWidth(180)  # Set minimum width
        self.select_output_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #0066cc;
                border: 2px solid #0066cc;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #e8e8ed;
            }
            QPushButton:pressed {
                background-color: #d1d1d6;
            }
        """)
        
        button_layout.addWidget(self.select_files_btn)
        button_layout.addWidget(self.select_output_btn)
        main_layout.addLayout(button_layout)
        
        # Password input field with improved styling
        password_layout = QHBoxLayout()
        password_layout.setSpacing(10)
        
        self.password_label = QLabel("Password (optional):")
        self.password_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.password_input = QLineEdit()
        self.password_input.setMinimumHeight(35)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #86868b;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #0066cc;
            }
        """)
        
        password_layout.addWidget(self.password_label)
        password_layout.addWidget(self.password_input)
        password_layout.addStretch()
        
        # Progress bar with improved styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #86868b;
                border-radius: 6px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                background-color: #f5f5f7;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 4px;
            }
        """)
        self.progress_bar.hide()
        
        # Auto-crack checkbox
        self.auto_crack_checkbox = QCheckBox("Try automatic password cracking if password fails")
        self.auto_crack_checkbox.setChecked(True)
        main_layout.addWidget(self.auto_crack_checkbox)
        
        # File list table
        self.file_table = QTableWidget(0, 3)  # rows, columns
        self.file_table.setHorizontalHeaderLabels(["File", "Status", "Message"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.file_table.setMinimumHeight(250)  # Increased minimum height
        self.file_table.verticalHeader().setDefaultSectionSize(35)  # Increased row height
        self.file_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 6px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        main_layout.addWidget(self.file_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: #f5f5f7;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 5px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Process button
        self.process_btn = QPushButton("Process Files")
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setMinimumHeight(50)
        self.process_btn.setMaximumWidth(300)  # Limit width to make it more compact
        self.process_btn.setEnabled(False)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px;  # Reduced padding
                font-size: 15px;  # Slightly smaller font
            }
            QPushButton:hover {
                background-color: #0055b3;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QPushButton:disabled {
                background-color: #86868b;
            }
        """)
        main_layout.addWidget(self.process_btn)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        if files:
            self.add_files(files)
            
    def add_files(self, files):
        # Add files to the list
        for file in files:
            if file not in self.pdf_files:
                self.pdf_files.append(file)
                
                # Add to table
                row = self.file_table.rowCount()
                self.file_table.insertRow(row)
                
                # File name
                filename = os.path.basename(file)
                self.file_table.setItem(row, 0, QTableWidgetItem(filename))
                
                # Status
                status_item = QTableWidgetItem("Pending")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.file_table.setItem(row, 1, status_item)
                
                # Message
                self.file_table.setItem(row, 2, QTableWidgetItem(""))
                
        # Enable process button if we have files
        self.process_btn.setEnabled(len(self.pdf_files) > 0)
        
    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_directory
        )
        if directory:
            self.output_directory = directory
            
    def process_files(self):
        if not self.pdf_files:
            return
            
        if self.processing_thread and self.processing_thread.isRunning():
            # Stop the current processing
            self.processing_thread.stop()
            self.process_btn.setText("Process Files")
            return
            
        # Update UI
        self.process_btn.setText("Stop Processing")
        self.progress_bar.setValue(0)
        
        # Reset status
        for row in range(self.file_table.rowCount()):
            status_item = QTableWidgetItem("Pending")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(row, 1, status_item)
            self.file_table.setItem(row, 2, QTableWidgetItem(""))
            
        # Start processing thread
        password = self.password_input.text()
        use_crack = self.auto_crack_checkbox.isChecked()
        
        self.processing_thread = PDFProcessingThread(
            self.pdf_files, self.output_directory, password, use_crack
        )
        
        # Connect signals
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.file_processed.connect(self.update_file_status)
        self.processing_thread.processing_finished.connect(self.processing_finished)
        
        # Start the thread
        self.processing_thread.start()
        
    def update_progress(self, current: int, total: int):
        """Update the progress bar"""
        percentage = int((current / total) * 100)
        self.progress_bar.setValue(percentage)
        
    def update_file_status(self, filename: str, success: bool, message: str):
        """Update the status of a processed file"""
        # Find the row for this file
        for row in range(self.file_table.rowCount()):
            if self.file_table.item(row, 0).text() == filename:
                # Update status
                status = "Success" if success else "Failed"
                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Set color based on status
                if success:
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                    
                self.file_table.setItem(row, 1, status_item)
                
                # Update message
                self.file_table.setItem(row, 2, QTableWidgetItem(message))
                break
                
    def processing_finished(self):
        """Called when all files have been processed"""
        self.process_btn.setText("Process Files")
        
        # Count successes and failures
        successes = 0
        failures = 0
        
        for row in range(self.file_table.rowCount()):
            status = self.file_table.item(row, 1).text()
            if status == "Success":
                successes += 1
            elif status == "Failed":
                failures += 1
                
        # Show completion message
        QMessageBox.information(
            self,
            "Processing Complete",
            f"Processed {successes + failures} files.\n\n"
            f"Successful: {successes}\n"
            f"Failed: {failures}"
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a clean look
    
    # Set application-wide stylesheet for Apple-like appearance
    app.setStyleSheet("""
        QWidget {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
        }
    """)
    
    window = PDFCrackerUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()