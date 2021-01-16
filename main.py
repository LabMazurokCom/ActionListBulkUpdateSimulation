class Action:
    def __init__(self, action_id):
        self._action_id = action_id

    @property
    def action_id(self):
        return self._action_id


class RemoveFolderAction (Action):
    def __init__(self):
        pass


class RemoveFileAction (Action):
    def __init__(self, action_id, params):
        super().__init__(action_id)
        self._path, self._prev_action_id = params

    @property
    def path(self):
        return self._path

    @property
    def prev_action_id(self):
        return self._prev_action_id


class ModifyFileAction (Action):
    def __init__(self, action_id, params):
        super().__init__(action_id)
        self._path, self._hash, self._prev_action_id = params

    @property
    def path(self):
        return self._path

    @property
    def hash(self):
        return self._hash

    @property
    def prev_action_id(self):
        return self._prev_action_id


class CreateFolderAction (Action):
    def __init__(self):
        pass


class RenameFileAction (Action):
    def __init__(self, action_id, params):
        super().__init__(action_id)
        self._old_path, self._new_path, self._hash, self._prev_action_id = params

    @property
    def old_path(self):
        return self._old_path

    @property
    def new_path(self):
        return self._new_path

    @property
    def prev_action_id(self):
        return self._prev_action_id

    @property
    def hash(self):
        return self._hash


class RenameFolderAction (Action):
    def __init__(self):
        pass


class NoSuchPathException (Exception):
    def __init__(self, path):
        self.path = path
        super().__init__(self.path)


class NoSuchVersionException (Exception):
    def __init__(self, path, version):
        self.path = path
        self.version = version
        super().__init__(self.path, self.version)


class NotEmptyFileRemoveException (Exception):
    def __init__(self, path):
        self.path = path
        self.path = path
        super().__init__(self.path)


class FileSystem:
    def __init__(self):
        self._root = Folder(None, 'root', 0)
        self._bulks = 1

    def __contains__(self, item):
        if len(item) == 0:
            return True
        cur_folder = self._root
        for folder in item[:-1]:
            if folder in cur_folder:
                cur_folder = cur_folder.folders[folder]
            else:
                return False
        return item[-1] in cur_folder

    def execute(self, action: Action):
        action_type = type(action)
        if action_type == RemoveFolderAction:
            pass
        if action_type == RemoveFileAction:
            self.execute_remove_file_action(action)
        if action_type == ModifyFileAction:
            self.execute_modify_file_action(action)
        if action_type == CreateFolderAction:
            pass
        if action_type == RenameFolderAction:
            pass
        if action_type == RenameFileAction:
            self.execute_rename_file_action(action)

    def execute_modify_file_action(self, action: ModifyFileAction):
        file = self.create_file_if_not_exists(action.path, self._bulks)
        file.add_version(action.prev_action_id, self._bulks + 1, action.action_id, action.hash)

    def execute_remove_file_action(self, action: RemoveFileAction):
        try:
            file = self.get_file(action.path)
            file.remove_version(action.prev_action_id)
            if file.is_empty():
                file.parent.remove_file(file.name)
        except NoSuchVersionException:
            pass
        except NoSuchPathException:
            pass

    def execute_rename_file_action(self, action: RenameFileAction):
        remove_action = RemoveFileAction(action.action_id, [action.old_path, action.prev_action_id])
        modify_action = ModifyFileAction(action.action_id,
                                         [action.new_path, action.hash, action.prev_action_id])
        self.execute_remove_file_action(remove_action)
        self.execute_modify_file_action(modify_action)

    def create_file_if_not_exists(self, path, bulk_number):
        parent_folder = self.create_folder_if_not_exists(path[:-1], bulk_number)
        return parent_folder.add_file_if_not_exists(path[-1], bulk_number)

    def create_folder_if_not_exists(self, path, bulk_number):
        cur_folder = self._root
        for folder in path:
            cur_folder = cur_folder.add_folder_if_not_exists(folder, bulk_number)
        return cur_folder

    def get_file(self, path):
        folder = self.get_folder(path[:-1])
        return folder.get_file(path[-1])

    def get_folder(self, path):
        cur_folder = self._root
        for folder in path:
            cur_folder = cur_folder.get_folder(folder)
        return cur_folder

    @staticmethod
    def is_file_path(item):
        return '.' in item[-1]


class Folder:
    def __init__(self, parent, name, bulk_number):
        self._parent = parent
        self._name = name
        self._folders = dict()
        self._files = dict()
        self.bulk_number = bulk_number

    def __contains__(self, item):
        if '.' in item:
            return item in self.files
        else:
            return item in self.folders

    @property
    def parent(self):
        return self._parent

    @property
    def name(self):
        return self._name

    @property
    def folders(self):
        return self._folders

    @property
    def files(self):
        return self._files

    def add_folder_if_not_exists(self, folder, bulk_number):
        if folder not in self:
            self.update_bulk_number(bulk_number)
            self.folders[folder] = Folder(self, folder, bulk_number)
        return self.folders[folder]

    def add_file_if_not_exists(self, file, bulk_number):
        if file not in self.files:
            self.bulk_number = bulk_number
            self.files[file] = File(self, file)
        return self.files[file]

    def file(self, file):
        return self.files[file]

    def get_folder(self, folder):
        return self.folders[folder]

    def remove_file(self, file_name, bulk_number):
        file = self.files[file_name]
        if not file.is_empty():
            raise NotEmptyFileRemoveException(str(file))
        self.update_bulk_number(bulk_number)
        del self.files[file]

    def __str__(self):
        parent_to_str = str(self.parent) if self.parent is not None else ""
        return parent_to_str + "/" + self.name

    def update_bulk_number(self, bulk_number):
        if self.bulk_number < bulk_number:
            self.bulk_number = bulk_number
            if self.parent is not None:
                self.parent.update_bulk_number(bulk_number)


class File:
    def __init__(self, parent: Folder, name):
        self._parent = parent
        self._name = name
        self._versions = dict()

    @property
    def parent(self):
        return self._parent

    @property
    def name(self):
        return self._name

    @property
    def versions(self):
        return self._versions

    def add_version(self, prev_action_id, bulk_number, action_id, hash):
        self.parent.update_bulk_number(bulk_number)
        if prev_action_id in self.versions:
            del self.versions[prev_action_id]
        self.versions[action_id] = FileVersion(self, bulk_number, action_id, hash)

    def remove_version(self, version, bulk_number):
        if version not in self.versions:
            raise NoSuchVersionException(str(self), version)
        self.parent.update_bulk_number(bulk_number)
        del self.versions[version]

    def is_empty(self):
        return len(self.versions) == 0

    def __str__(self):
        return str(self.parent) + "/" + self.name


class FileVersion:
    def __init__(self, file: File, bulk_number, action_id, hash):
        self._file = file
        self._bulk_number = bulk_number
        self._action = action_id
        self._hash = hash

    @property
    def file(self):
        return self._file

    @property
    def bulk_number(self):
        return self._bulk_number

    @property
    def get_action_id(self):
        return self._action

    @property
    def get_hash(self):
        return self._hash


class ActionListExecutor:
    def __init__(self):
        pass
