try:
    # required for Ubuntu 20.04 since there a system library is too old for pyqt6 and the import fails
    # when not importing this, one can still use the map conversion
    from PyQt6.QtWidgets import QMessageBox, QWidget

    pyqt_available = True

    def _message(
        widget: QWidget,
        title: str,
        text: str,
        buttons=QMessageBox.StandardButton.Ok,
        default_button=QMessageBox.StandardButton.Ok,
    ) -> QMessageBox.StandardButton:
        messagebox = QMessageBox()
        reply = messagebox.warning(widget, title, text, buttons, default_button)
        messagebox.close()
        return reply

    def error(
        widget: QWidget, text: str, buttons=QMessageBox.StandardButton.Ok, default_button=QMessageBox.StandardButton.Ok
    ) -> QMessageBox.StandardButton:
        return _message(widget, "Error", text, buttons, default_button)

    def warning(
        widget: QWidget, text: str, buttons=QMessageBox.StandardButton.Ok, default_button=QMessageBox.StandardButton.Ok
    ) -> QMessageBox.StandardButton:
        return _message(widget, "Warning", text, buttons, default_button)

except (ImportError, RuntimeError):
    pyqt_available = False
