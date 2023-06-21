from crdesigner.map_conversion.osm2cr import config


class StreetTypesMainController:
    """
    Window to select types of roads
    """

    def __init__(self, mwindow):
        pass

    def accept(self) -> None:
        """
        accepts the values set in the window and saves them to config.py
        then closes the dialog

        :return: None
        """
        self.save()
        self.original_accept()

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        all_accepted_highways = config_default.ACCEPTED_HIGHWAYS_MAINLAYER.copy()
        all_accepted_highways.extend(config_default.ACCEPTED_HIGHWAYS_SUBLAYER)
        for highway_type in all_accepted_highways:
            types[getattr(self.dialog.ui, 'chk_' + highway_type)] = highway_type
        config.ACCEPTED_HIGHWAYS_MAINLAYER = [current_type for check_box, current_type in types.items() if
                                              check_box.isChecked()]

        self.save_to_custom_settings()

    def save_to_custom_settings(self):
        path_to_custom_settings_osm2cr = os.path.join(ROOT_DIR, 'custom_settings_osm2cr.yaml')

        with open(path_to_custom_settings_osm2cr) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        data['accepted_highways_mainlayer'] = config.ACCEPTED_HIGHWAYS_MAINLAYER
        with open(path_to_custom_settings_osm2cr, 'w') as yaml_file:
            yaml_file.write(yaml.dump(data, default_flow_style=False))


class LaneCountsController:
    """
    Window to edit counts of lanes for street types
    """

    def __init__(self, mwindow):
        pass

    def accept(self) -> None:
        """
        saves values to config.py and closes dialog

        :return: None
        """
        self.save()
        self.original_accept()

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        for highway_type in list(config.LANECOUNTS.keys()):
            types[getattr(self.dialog.ui, 'sb_' + highway_type)] = highway_type
        config.LANECOUNTS = {current_type: spin_box.value() for spin_box, current_type in types.items()}
        self.save_to_custom_settings()

    def save_to_custom_settings(self):
        '''
        saves lane counts changed configs to yaml file to be persistent
        '''
        path_to_custom_settings_osm2cr = os.path.join(ROOT_DIR, 'custom_settings_osm2cr.yaml')

        with open(path_to_custom_settings_osm2cr) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        for key in config.LANECOUNTS:
            data['lanecounts'][key] = config.LANECOUNTS[key]
        with open(path_to_custom_settings_osm2cr, 'w') as yaml_file:
            yaml_file.write(yaml.dump(data, default_flow_style=False))


class LaneWidthController:
    """
    Window to edit width of lanes for street types
    """

    def __init__(self, mwindow):
        pass

    def accept(self) -> None:
        """
        saves values to config.py and closes dialog

        :return: None
        """
        self.save()
        self.original_accept()

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        for highway_type in list(config.LANEWIDTHS.keys()):
            types[getattr(self.dialog.ui, 'sb_' + highway_type)] = highway_type
        config.LANEWIDTHS = {current_type: spin_box.value() for spin_box, current_type in types.items()}
        self.save_to_custom_settings()

    def save_to_custom_settings(self):
        '''
        saves Lane widths changed configs to yaml file to be persistent
        '''
        path_to_custom_settings_osm2cr = os.path.join(ROOT_DIR, 'custom_settings_osm2cr.yaml')

        with open(path_to_custom_settings_osm2cr) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        for key in config.LANECOUNTS:
            data['lanewidths'][key] = config.LANEWIDTHS[key]
        with open(path_to_custom_settings_osm2cr, 'w') as yaml_file:
            yaml_file.write(yaml.dump(data, default_flow_style=False))


class SpeedLimitsController:
    """
    Window to edit speed limits for street types
    """

    def __init__(self, mwindow):
        pass

    def accept(self) -> None:
        """
        saves values to config.py and closes dialog

        :return: None
        """
        self.save()
        self.original_accept()

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        for highway_type in list(config.SPEED_LIMITS.keys()):
            types[getattr(self.dialog.ui, 'sb_' + highway_type)] = highway_type
        config.SPEED_LIMITS = {current_type: spin_box.value() for spin_box, current_type in types.items()}
        self.save_to_custom_settings()

    def save_to_custom_settings(self):
        '''
        saves speed limits changed configs to yaml file to be persistent
        '''
        path_to_custom_settings_osm2cr = os.path.join(ROOT_DIR, 'custom_settings_osm2cr.yaml')

        with open(path_to_custom_settings_osm2cr) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        for key in config.LANECOUNTS:
            data['speed_limits'][key] = config.SPEED_LIMITS[key]
        with open(path_to_custom_settings_osm2cr, 'w') as yaml_file:
            yaml_file.write(yaml.dump(data, default_flow_style=False))


class StreetTypesSubController:
    """
    Window to edit sublayer way types
    """

    def __init__(self, mwindow):
        pass

    def accept(self) -> None:
        """
        accepts the values set in the window and saves them to config.py
        then closes the dialog

        :return: None
        """
        self.save()

        self.original_accept()

    def save(self) -> None:
        """
        saves values of checkboxes to config.py

        :return: None
        """
        types = dict()
        all_accepted_highways = config_default.ACCEPTED_HIGHWAYS_MAINLAYER.copy()
        all_accepted_highways.extend(config_default.ACCEPTED_HIGHWAYS_SUBLAYER)
        for highway_type in all_accepted_highways:
            types[getattr(self.dialog.ui, 'chk_' + highway_type)] = highway_type
        config.ACCEPTED_HIGHWAYS_SUBLAYER = [current_type for check_box, current_type in types.items() if
                                             check_box.isChecked()]
        self.save_to_custom_settings()

    def save_to_custom_settings(self):
        path_to_custom_settings_osm2cr = os.path.join(ROOT_DIR, 'custom_settings_osm2cr.yaml')

        with open(path_to_custom_settings_osm2cr) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        data['accepted_highways_sublayer'] = config.ACCEPTED_HIGHWAYS_SUBLAYER
        with open(path_to_custom_settings_osm2cr, 'w') as yaml_file:
            yaml_file.write(yaml.dump(data, default_flow_style=False))
