from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class UIFeedbackBridge(QObject):
    update_signal = pyqtSignal(object)

    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.update_signal.connect(self._handle_update)
        
    def _handle_update(self, fn):
        fn()

    def update_ui(self, fn):
        self.update_signal.emit(fn)
