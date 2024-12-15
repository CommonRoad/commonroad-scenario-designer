from PyQt6.QtWidgets import QSizePolicy


def create_size_policy_for_settings_elements():
    """
    The default size policy of QLineEdit behaves differently than the one of QSpinBox; in particular, it has a higher
    width. But as we want a unified appearance, we take the one of QSpinBox for QLineEdit, which is returned by
    this function.
    """
    return QSizePolicy(
        QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed, QSizePolicy.ControlType.SpinBox
    )
