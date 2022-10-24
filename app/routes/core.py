from schemas.core import ErrorSchema

responses = {
    'HTTP_400': ErrorSchema,
    'HTTP_403': ErrorSchema,
    'HTTP_404': ErrorSchema,
    'HTTP_409': ErrorSchema,
}
