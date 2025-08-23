

class NameValidator:
    @staticmethod
    def check_valid(name: str) -> None:
        """
        Проверяет, что имя схемы содержит только допустимые имена.

        Args:
            name (str): Имя схемы.

        Raises:
            ValueError: Если имя содержит недопустимые символы / пустое.
        """
        __tracebackhide__ = True
        
        # Валидация имени схемы
        if not name or not isinstance(name, str):
            raise ValueError("Schema name must be a non-empty string")

        invalid_chars = '<>:"/\\|?*'
        if any(char in name for char in invalid_chars):
            raise ValueError(f"Schema name contains invalid characters: {invalid_chars}")
