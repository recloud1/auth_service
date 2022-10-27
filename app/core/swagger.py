from spectree import SpecTree, SecurityScheme

security_schemes = [
    SecurityScheme(name='jwt', data={'type': 'apiKey', 'name': 'Authorization', 'in': 'header'})
]

api = SpecTree(
    backend_name='flask',
    title='Сервис авторизации пользователей в рамках системы кинотеатра',
    annotations=True,
    security_schemes=security_schemes
)
