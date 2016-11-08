import json

n = int(input('Index File Count: '))

while True:
    k = input('Search for: ')
    res = []
    for i in range(n):
        with open('indices' + str(i+1), 'r') as f:
            indices = json.load(f)
            if k in indices:
                for v in indices[k]:
                    res.append(v)
                    
    for v in sorted(res, reverse=True):
        print(v)
