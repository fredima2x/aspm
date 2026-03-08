from PyQt5.QtWidgets import QScrollArea, QApplication
from PyQt5.QtCore import Qt, QEvent, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QWheelEvent

class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.setDuration(200)  # ms – niedriger = schneller

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        steps = delta / 120          # 1 Schritt = 120 Einheiten
        pixels = steps * 60          # wie weit pro Scroll-Schritt (anpassbar)

        scroll_bar = self.verticalScrollBar()

        # Laufende Animation sanft weiterführen statt neu starten
        current_target = self._animation.endValue()
        if self._animation.state() == QPropertyAnimation.Running and current_target is not None:
            new_target = current_target - pixels
        else:
            new_target = scroll_bar.value() - pixels

        # Ziel auf gültigen Bereich begrenzen
        new_target = max(scroll_bar.minimum(), min(int(new_target), scroll_bar.maximum()))

        self._animation.stop()
        self._animation.setStartValue(scroll_bar.value())
        self._animation.setEndValue(new_target)
        self._animation.start()