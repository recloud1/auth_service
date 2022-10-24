from spectree import SpecTree, SecurityScheme

security_schemes = [
    SecurityScheme(name='jwt', data={'type': 'apiKey', 'name': 'Authorization', 'in': 'header'})
]

api = SpecTree('flask', annotations=True, security_schemes=security_schemes)
