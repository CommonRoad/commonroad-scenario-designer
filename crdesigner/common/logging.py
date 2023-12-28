import functools
from datetime import datetime

from crdesigner.common.config.gui_config import gui_config
from crdesigner.ui.gui.autosaves.autosaves_setup import DIR_AUTOSAVE


class Logger:
    def __init__(self):
        self.fully_initialized = False
        self.first_stacks = ""
        self.first_stack_saved = False

    def log(self, func):
        """
        loggs a function to a logging file with the arguments and time
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if gui_config.logging():
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
                time = datetime.now()

                if not self.fully_initialized:
                    self.first_stacks = self.first_stacks + (
                        f"{time.strftime('%d-%b-%y %H:%M:%S')} - "
                        f"Function {func.__name__} was called with args {signature} \n"
                    )

                elif not self.first_stack_saved:
                    self.first_stacks = self.first_stacks + (
                        f"{time.strftime('%d-%b-%y %H:%M:%S')} - "
                        f"Function {func.__name__} was called with args {signature}"
                    )
                    with open(DIR_AUTOSAVE + "/logging_file.txt", "a+") as file_object:
                        file_object.write(self.first_stacks)
                        file_object.write("\n")

                    self.first_stack_saved = True

                else:
                    with open(DIR_AUTOSAVE + "/logging_file.txt", "a+") as file_object:
                        file_object.write(
                            f"{time.strftime('%d-%b-%y %H:%M:%S')} - Function {func.__name__} "
                            f"was called with args {signature}"
                        )
                        file_object.write("\n")

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                print(
                    f"There has been an error with the Function {func.__name__} with args {signature} with "
                    f"the actions: {str(e)}"
                )

        return wrapper

    def set_initialized(self):
        self.fully_initialized = True


logger = Logger()
