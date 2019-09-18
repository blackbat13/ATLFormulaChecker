class FileTools:
    @staticmethod
    def save_to_file(file_name: str, content: str, extension: str = "ispl") -> str:
        """Saves file with the given name, content and extension
        :param file_name: name of the file
        :param content: content of the file
        :param extension: extension of the file
        :return: name of the created file
        """
        file_name = FileTools.add_extension(file_name, extension)
        f = open(f"{file_name}", "w")
        f.write(content)
        f.close()
        return file_name

    @staticmethod
    def add_extension(file_name: str, extension: str) -> str:
        """Adds extension to the file name if not present
        :param file_name: name of the file
        :param extension: extension of the file
        :return: file name with the given extension
        """
        if file_name.endswith("." + extension):
            return file_name
        else:
            return file_name + "." + extension
