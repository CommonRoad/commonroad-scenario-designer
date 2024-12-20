from PyQt6.QtWidgets import QMessageBox, QWidget


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
    widget: QWidget,
    text: str,
    buttons=QMessageBox.StandardButton.Ok,
    default_button=QMessageBox.StandardButton.Ok,
) -> QMessageBox.StandardButton:
    return _message(widget, "Error", text, buttons, default_button)


def warning(
    widget: QWidget,
    text: str,
    buttons=QMessageBox.StandardButton.Ok,
    default_button=QMessageBox.StandardButton.Ok,
) -> QMessageBox.StandardButton:
    return _message(widget, "Warning", text, buttons, default_button)
