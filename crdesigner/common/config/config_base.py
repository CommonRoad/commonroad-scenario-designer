import copy
import os
from typing import Callable, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

import yaml
from PyQt6.QtCore import QObject, pyqtSignal

try:
    # required for Ubuntu 20.04 since there a system library is too old for pyqt6 and the import fails
    # when not importing this, one can still use the map conversion
    from PyQt6.QtWidgets import QMessageBox

    pyqt_available = True
except (ImportError, RuntimeError):
    pyqt_available = False

from crdesigner.ui.gui.utilities.custom_yaml import add_custom_interval_interpreter

T = TypeVar("T")


add_custom_interval_interpreter()


class Attribute(Generic[T], QObject):
    """Attribute class for the settings. This class is used to define the attributes of the settings model.
    It is used to define the type of the attribute, the default value, the display name, the description, the unit,
    the options, and the validation function.

    :ivar attribute_changed: signal to subscribe to if the value of the attribute has changed. Subscription
        is done via the subscribe method.
    """

    attribute_changed = pyqtSignal()

    def __init__(
        self,
        value: T,
        display_name: str = "",
        description: str = "",
        unit: str = "",
        options: Optional[Union[Tuple[T, T], List[T]]] = None,
        validation: Optional[Callable[[T], bool]] = None,
    ):
        """Constructor of the attribute class.
        :param value: The value of the attribute. This is also used as the default value.
        :param display_name: The display name of the attribute. This is used in the GUI.
        :param description: The description of the attribute. This is used in the GUI as a tooltip.
        :param unit: The unit of the attribute. This is used in the GUI and could be "m" or "m/s" for example.
        :param options: The options of the attribute. This is used in the GUI as a combobox. The user can choose from
            the options provided here. The value has to be one of the options.
        :param validation: The validation function of the attribute. This is used to validate the value of the
            attribute. Validation is done when the user clicks the "Save" button in the GUI. If the validation
            function returns False, a warning message is shown and the saving is cancelled.
        """
        super().__init__()

        self.value = value
        self.default = copy.deepcopy(value)
        self.last_saved = copy.deepcopy(value)
        self.display_name = display_name
        self.description = description
        self.unit = unit
        self.value_type = type(value)
        self.options = options
        self.validation = validation

        if self.options is not None:
            if self.value not in self.options:
                raise ValueError(f"Invalid value {self.value} for attribute {self.display_name}")

    def __get__(self, instance, owner) -> T:
        """Returns the value of the attribute.
        :param instance: The instance of the class. This is not used and not relevant for the intended use.
        :param owner: The owner of the class. This is not used and not relevant for the intended use.
        :return: The value of the attribute.
        """
        return self.value

    def __set__(self, instance, value: T):
        """Sets the value of the attribute to the given value. This function is used to set the value from the GUI.
        :param instance: The instance of the class. This is not used and not relevant for the intended use.
        :param value: The value to set the attribute to.
        """
        if not isinstance(value, self.value_type) and value is not None:
            raise TypeError(
                f"Expected type {self.value_type} for attribute {self.display_name}, got {type(value)}"
            )
        if self.options is not None:
            if value not in self.options:
                self._warning_wrong_setting()
                return
        self.value = copy.deepcopy(value)

    def validate(self) -> bool:
        """Validates the value of the attribute. If the value is invalid, a warning message is shown and
        the value is reset to the last saved value.
        :return: True if the value is valid, False otherwise.
        """
        if self.validation is not None:
            if not self.validation(self.value):
                self._warning_wrong_setting()
                self.value = copy.deepcopy(self.last_saved)
                return False
        return True

    def reset(self):
        """Resets the value of the attribute to the default value."""
        if self.value != self.default:
            self.value = copy.deepcopy(self.default)
            self.notify()

    def is_default(self) -> bool:
        """
        Returns True if the value of the attribute is equal to the default value, False otherwise.
        """
        return self.value == self.default

    def set_value(self, param):
        """Sets the value of the attribute to the given value. This function is used to set the value from the GUI.
        :param param: The value to set the attribute to.
        """
        self.value = param

    def subscribe(self, callback: Callable[[T], None]):
        """Subscribes to the attribute_changed signal. The callback function is called when the value of the attribute.
        has changed.
        :param callback: The callback function to call when the value of the attribute has changed. The current value
            of the attribute is passed to the callback function. The callback function has to accept one parameter.
        """
        self.attribute_changed.connect(lambda: callback(self.value))

    def disconnect_methods(self):
        self.attribute_changed.disconnect()

    def notify(self):
        """Notifies all subscribers of this Attribute that the value has changed."""
        self.attribute_changed.emit()

    def save_last_value(self):
        """Saves the current value of the attribute as the last saved value. This is used to restore the last saved."""
        self.last_saved = copy.deepcopy(self.value)

    def restore_last_value(self):
        """Restores the last saved value of the attribute as the current value."""
        self.value = copy.deepcopy(self.last_saved)

    def _warning_wrong_setting(self):
        if pyqt_available:
            warning_dialog = QMessageBox()
            warning_dialog.warning(
                None,
                "Warning",
                f"Setting {self.display_name} contains invalid value!",
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Ok,
            )
            warning_dialog.close()
        self.reset()


class ConfigValueInstance:
    """
    This class can be used to have an instance of the values of a specific config decoupled from the
    singleton instance. Changes made to the instance will not be reflected in the singleton instance.

    This can be especially useful if you want to have a config instance that holds specific values for a
    specific use case, and you don't want to change the values of the singleton instance.
    """


class BaseConfig:
    """
    This class is the base class for all settings classes. It provides the functionality to save and restore
    settings to and from a yaml file.
    :ivar LAYOUT: This variable is a list of lists of attributes or labels (str). The first list represents the
    columns of the settings dialog. The second list represents the rows in those columns.
    :ivar CUSTOM_SETTINGS_PATH: This variable is the path to the yaml file where the settings are saved to.
    """

    LAYOUT: List[List[Union[Attribute, str]]] = None
    CUSTOM_SETTINGS_PATH: Attribute[str] = None

    def validate_all_settings(self) -> bool:
        """This function will validate all settings of the derived settings class. If a setting is invalid, a warning
        message is shown and the value is reset to the last saved value.
        :return: True if all settings are valid, False otherwise.
        """
        all_valid = True
        for _, attr in vars(type(self)).items():
            if isinstance(attr, Attribute):
                if not attr.validate():
                    all_valid = False
        return all_valid

    def save_to_yaml_file(self):
        """This function will save the none default settings of the derived settings class to a yaml file,
        which is specified by the file_path."""
        if isinstance(self.CUSTOM_SETTINGS_PATH, str):
            yaml_path = self.CUSTOM_SETTINGS_PATH
        else:
            yaml_path = self.CUSTOM_SETTINGS_PATH.value

        # first read the yaml file, if it exists, remove all occurrences of attributes from the
        # yaml file, which belong to the derived settings class then write the yaml file again
        settings = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                settings = yaml.load(f, Loader=yaml.FullLoader)
            if settings is not None:
                for attr_name in vars(type(self)).keys():
                    if attr_name in settings:
                        del settings[attr_name]
            else:
                settings = {}

        settings.update(self._get_none_default_settings())

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(settings, f)

    def restore_from_yaml_file(self):
        """This function will restore the none default settings of the derived settings class from a yaml file,
        which is specified by the file_path."""
        if isinstance(self.CUSTOM_SETTINGS_PATH, str):
            yaml_path = self.CUSTOM_SETTINGS_PATH
        else:
            yaml_path = self.CUSTOM_SETTINGS_PATH.value

        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                settings = yaml.load(f, Loader=yaml.FullLoader)
            if settings is None:
                # if no custom settings were saved, they have to be default
                self.reset_settings()
            else:
                self._set_settings(settings)

        else:
            # if the yaml file does not exist, the settings have to be default
            self.reset_settings()
        self.notify_all()

    def reset_settings(self):
        """This function will reset all settings of the derived settings class to their default values."""
        for _, attr in vars(type(self)).items():
            if isinstance(attr, Attribute):
                attr.reset()

    def backup_settings(self):
        """This function will save the current values of all attributes of the derived settings class."""
        for _, attr in vars(type(self)).items():
            if isinstance(attr, Attribute):
                attr.save_last_value()

    def restore_settings(self):
        """This function will restore the last saved values of all attributes of the derived settings class."""
        for _, attr in vars(type(self)).items():
            if isinstance(attr, Attribute):
                attr.restore_last_value()

    def notify_all(self):
        """This function will notify all attributes of the derived settings class."""
        for _, attr in vars(type(self)).items():
            if isinstance(attr, Attribute):
                attr.notify()

    def _get_none_default_settings(self) -> dict:
        """This function will return a dictionary with the none default settings of the derived settings class."""
        return {
            name: attr.value
            for name, attr in vars(type(self)).items()
            if isinstance(attr, Attribute) and not attr.is_default()
        }

    def _set_settings(self, settings: dict):
        """This function will set the settings of the derived settings class from a dictionary."""
        config_attributes = vars(type(self))
        for key, value in settings.items():
            attr = config_attributes.get(key)
            if isinstance(attr, Attribute) and key in config_attributes:
                attr.set_value(value)

    def get_attribute(self, name: str) -> Attribute:
        """This function will return the attribute with the given name.
        :param name: The name of the attribute.
        :return: The attribute with the given name.
        """
        attr = vars(type(self)).get(name)
        if isinstance(attr, Attribute):
            return attr

        raise KeyError(f"Unknown setting {name}")

    def value_instance(self, values: Dict[str, T] = None) -> ConfigValueInstance:
        """This function will return a ConfigValueInstance with the same values as the attribute with the given name.
        :param values: A dictionary with the values to override the currently set values of the config.
        """
        instance = ConfigValueInstance()
        for name, attr in vars(type(self)).items():
            if isinstance(attr, Attribute):
                if values is not None and name in values:
                    setattr(instance, name, values[name])
                else:
                    setattr(instance, name, copy.deepcopy(attr.value))

        return instance

    def default_instance(self, values: Dict[str, T] = None) -> ConfigValueInstance:
        """This function will return a ConfigValueInstance with the default values of the attribute with the given name.
        :param values: A dictionary with values to overwrite the default values.
        """
        instance = ConfigValueInstance()
        for name, attr in vars(type(self)).items():
            if isinstance(attr, Attribute):
                if values is not None and name in values:
                    setattr(instance, name, values[name])
                else:
                    setattr(instance, name, copy.deepcopy(attr.default))

        return instance


Config = Type[Union[BaseConfig, ConfigValueInstance]]
