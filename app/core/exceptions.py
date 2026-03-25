class AppError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class BadRequestError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=400)


class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(detail=detail, status_code=401)


class NotFoundError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=404)


class ConflictError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=409)
