def menu(food, *args, **kwsrgs):
    for k, v in kwsrgs.items():
        print(k, v)


d = {
    'entree': 'beef',
    'drink': 'ice coffee',
    'dessert': 'ice'
}
menu(**d)
