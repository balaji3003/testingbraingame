import sys
import os
import csv
from PyQt5 import QtWidgets, QtCore, QtGui

class BirdFlyingGame(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Get screen dimensions and set minimum size to 50% of monitor
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        min_width = int(screen.width() * 0.5)
        min_height = int(screen.height() * 0.5)
        
        self.setWindowTitle("Bird Flying Game")
        self.setMinimumSize(min_width, min_height)
        
        # Main widget and layout
        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Control panel at top
        self.control_panel = QtWidgets.QFrame()
        self.control_panel.setStyleSheet("background-color: #E0E0E0; padding: 5px;")
        self.control_layout = QtWidgets.QHBoxLayout(self.control_panel)
        
        # Timer display
        self.timer_label = QtWidgets.QLabel("Time: 0.0s | Score: 0")
        self.timer_label.setStyleSheet("font: bold 16px;")
        self.control_layout.addWidget(self.timer_label)
        
        # Add to main layout
        self.layout.addWidget(self.control_panel)
        
        # Game area
        self.game_area = QtWidgets.QGraphicsView()
        self.game_area.setStyleSheet("background-color: skyblue; border: none;")
        self.game_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.game_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.game_area)
        
        # Game elements
        self.scene = QtWidgets.QGraphicsScene()
        self.game_area.setScene(self.scene)
        
        # Load bird image or create fallback
        self.bird_pixmap = QtGui.QPixmap("bird.png")
        if self.bird_pixmap.isNull():
            self.bird_pixmap = QtGui.QPixmap(40, 40)
            self.bird_pixmap.fill(QtGui.QColor(255, 215, 0))
        
        self.bird = QtWidgets.QGraphicsPixmapItem(self.bird_pixmap)
        self.scene.addItem(self.bird)
        
        # Game variables
        self.game_time = 0.0
        self.score = 0
        self.game_active = False
        self.score_records = []
        self.last_mouse_y = 0
        self.mouse_control_active = False
        self.bird_speed = 3
        self.bird_x = 100
        self.bird_y = 0
        self.current_second = 0
        self.max_zone_this_second = 0
        self.mouse_button_pressed = False
        
        # Zone indicators (visual feedback)
        self.zone_rects = []
        self.create_zones()
        
        # Timers
        self.game_timer = QtCore.QTimer()
        self.game_timer.timeout.connect(self.update_game)
        
        self.clock_timer = QtCore.QTimer()
        self.clock_timer.timeout.connect(self.update_timer)
        
        # Event filters
        self.game_area.viewport().installEventFilter(self)
        
    def create_zones(self):
        """Create visual zone indicators"""
        self.scene.clear()
        self.bird = QtWidgets.QGraphicsPixmapItem(self.bird_pixmap)
        self.scene.addItem(self.bird)
        
        height = self.game_area.height()
        zone_height = height / 10
        
        colors = [
            QtGui.QColor(255, 0, 0, 30),    # Zone 1 (Red)
            QtGui.QColor(255, 128, 0, 30),   # Zone 2
            QtGui.QColor(255, 255, 0, 30),   # Zone 3
            QtGui.QColor(128, 255, 0, 30),   # Zone 4
            QtGui.QColor(0, 255, 0, 30),     # Zone 5 (Green)
            QtGui.QColor(0, 255, 128, 30),   # Zone 6
            QtGui.QColor(0, 255, 255, 30),   # Zone 7
            QtGui.QColor(0, 128, 255, 30),   # Zone 8
            QtGui.QColor(0, 0, 255, 30),     # Zone 9
            QtGui.QColor(128, 0, 255, 30)    # Zone 10 (Purple)
        ]
        
        for i in range(10):
            rect = self.scene.addRect(
                0, i * zone_height, 
                self.game_area.width(), zone_height,
                pen=QtGui.QPen(QtCore.Qt.NoPen),
                brush=QtGui.QBrush(colors[i]))
            self.zone_rects.append(rect)
        
        # Add bird back on top
        self.scene.removeItem(self.bird)
        self.scene.addItem(self.bird)
        
    def resizeEvent(self, event):
        """Handle window resizing"""
        self.scene.setSceneRect(0, 0, self.game_area.width(), self.game_area.height())
        self.create_zones()
        super().resizeEvent(event)
        
    def eventFilter(self, source, event):
        """Track mouse movements and button presses"""
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.mouse_button_pressed = True
            
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            self.mouse_button_pressed = False
            
        if event.type() == QtCore.QEvent.MouseMove:
            mouse_pos = event.pos()
            view_pos = self.game_area.mapFromGlobal(self.mapToGlobal(mouse_pos))
            scene_pos = self.game_area.mapToScene(view_pos)
            self.last_mouse_y = scene_pos.y()
            
        return super().eventFilter(source, event)
        
    def keyPressEvent(self, event):
        """Handle spacebar to start/stop game"""
        if event.key() == QtCore.Qt.Key_Space:
            if not self.game_active:
                self.start_game()
            else:
                self.end_game()
        super().keyPressEvent(event)
        
    def start_game(self):
        """Start the game"""
        self.game_active = True
        self.game_time = 0.0
        self.score = 0
        self.score_records = []
        self.current_second = 0
        self.max_zone_this_second = 0
        
        # Position bird in middle
        self.bird_y = self.game_area.height() / 2
        self.bird_x = 100
        self.bird.setPos(self.bird_x, self.bird_y)
        
        # Start timers
        self.game_timer.start(16)  # ~60fps
        self.clock_timer.start(100)  # 10 times per second
        
        self.timer_label.setText("Time: 0.0s | Score: 0 | Game Active (SPACE to stop)")
        
    def update_timer(self):
        """Update the game timer"""
        if self.game_active:
            self.game_time += 0.1
            self.timer_label.setText(f"Time: {self.game_time:.1f}s | Score: {self.score} | Game Active (SPACE to stop)")
            
            # Auto-end after 1 minute
            if self.game_time >= 60.0:
                self.end_game()
                
    def update_game(self):
        """Main game update loop"""
        if not self.game_active:
            return
            
        # Continuous horizontal movement
        self.bird_x += self.bird_speed
        if self.bird_x > self.game_area.width():
            self.bird_x = -40  # Reset to left side at same height
            
        # Vertical movement controlled by mouse (only when button is pressed)
        if self.mouse_button_pressed:
            target_y = self.last_mouse_y - 20  # Offset to center bird on cursor
            self.bird_y += (target_y - self.bird_y) * 0.1  # Smooth follow
            
        # Keep bird in bounds
        self.bird_y = max(0, min(self.bird_y, self.game_area.height() - 40))
        self.bird.setPos(self.bird_x, self.bird_y)
        
        # Calculate current zone (1-10 from bottom to top)
        zone_height = self.game_area.height() / 10
        current_zone = 10 - min(9, int(self.bird_y / zone_height))
        
        # Track maximum zone reached each second
        new_second = int(self.game_time)
        if new_second > self.current_second:
            # Record the maximum zone from the previous second
            if self.current_second >= 0:  # Skip the first transition
                self.score += self.max_zone_this_second
                self.score_records.append((self.current_second, self.max_zone_this_second, self.score))
            
            # Reset for new second
            self.current_second = new_second
            self.max_zone_this_second = current_zone
        else:
            # Update maximum zone for current second
            if current_zone > self.max_zone_this_second:
                self.max_zone_this_second = current_zone
        
    def end_game(self):
        """End the game and save results"""
        self.game_active = False
        self.game_timer.stop()
        self.clock_timer.stop()
        
        # Record the final second's data
        if self.current_second >= 0:
            self.score += self.max_zone_this_second
            self.score_records.append((self.current_second, self.max_zone_this_second, self.score))
        
        # Save to CSV - one row per second with highest zone
        filename = f"bird_game_results_{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.csv"
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Time (s)', 'Zone', 'Total Score'])
            for record in self.score_records:
                writer.writerow(record)
        
        # Show final message
        self.timer_label.setText(f"Time: {self.game_time:.1f}s | Final Score: {self.score} | Results saved to {filename}")
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Game Over")
        msg.setText(f"Final Score: {self.score}\n\nResults saved to:\n{filename}")
        msg.exec_()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Check if bird.png exists
    if not os.path.exists("bird.png"):
        print("Note: bird.png not found - using colored circle instead")
    
    game = BirdFlyingGame()
    game.show()
    sys.exit(app.exec_())