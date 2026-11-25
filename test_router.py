from backend.router import route

tests = [
    "Optimize my resume for Google",
    "Translate this to Spanish for the Mexican market",
    "Make my skills section more relevant for a data scientist role",
    "Make my summary stronger and then translate to French",
    "What is a good resume length?",
]
for m in tests:
    print(m, "->", route(m, [], False))