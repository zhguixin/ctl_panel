git clone ssh://git@219.245.82.2/lte-sat.git  # 默认从服务器上检出dev分支

$ git checkout -b feature_001  #本地基于dev分支创建feature_001分支, 并自动切换本地至feature_001分支
$ 编辑代码
$ git add ...
$ git commit -m "...." 
$ git checkout dev
$ git merge --no-ff -m "...." feature_001
$ git push -u origin dev   #将修改推送到服务器上