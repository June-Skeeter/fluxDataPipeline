import os
pth = os.path.join(os.path.split(__file__)[0],'scripts','submodules')
req = []
for submodule in os.listdir(pth):
    with open(os.path.join(pth,submodule,'requirements.in')) as f:
        req = req + f.read().split('\n')
req = set(req)
with open(os.path.join(os.path.split(__file__)[0],'requirements.in'), 'w+') as f:
    f.write('\n'.join(req))