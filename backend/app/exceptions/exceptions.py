class AuthenticationError(Exception):
    def __init__(self, message="Authentication failed", code="AUTHENTICATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthorizationError(Exception):
    def __init__(self, message="Access denied", code="AUTHORIZATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(Exception):
    def __init__(self, message="Validation failed", code="VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class UserAlreadyExistsError(Exception):
    def __init__(self, message="User already exists", code="USER_ALREADY_EXISTS"):
        self.message = message
        self.code = code
        super().__init__(message)


class UserNotFoundError(Exception):
    def __init__(self, message="User not found", code="USER_NOT_FOUND"):
        self.message = message
        self.code = code
        super().__init__(message)


class InvalidCredentialsError(Exception):
    def __init__(self, message="Invalid username or password", code="INVALID_CREDENTIALS"):
        self.message = message
        self.code = code
        super().__init__(message)


class MessageError(Exception):
    def __init__(self, message="Message error", code="MESSAGE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class AttachmentError(Exception):
    def __init__(self, message="Attachment error", code="ATTACHMENT_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class FileTooLargeError(Exception):
    def __init__(self, message="File too large", code="FILE_TOO_LARGE"):
        self.message = message
        self.code = code
        super().__init__(message)


class UnsupportedFileTypeError(Exception):
    def __init__(self, message="Unsupported file type", code="UNSUPPORTED_FILE_TYPE"):
        self.message = message
        self.code = code
        super().__init__(message)


class ConversationNotFoundError(Exception):
    def __init__(self, message="Conversation not found", code="CONVERSATION_NOT_FOUND"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotConversationMemberError(Exception):
    def __init__(self, message="You are not a member of this conversation", code="NOT_CONVERSATION_MEMBER"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotGroupOwnerError(Exception):
    def __init__(self, message="Only the group owner can perform this action", code="NOT_GROUP_OWNER"):
        self.message = message
        self.code = code
        super().__init__(message)


class ConversationError(Exception):
    def __init__(self, message="Conversation error", code="CONVERSATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)
