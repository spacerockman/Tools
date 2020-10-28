## Basic 
$ git init

$ git config -l

$ git config --global user.name "EricXu"

$ git config --global user.email "test@test.com"

$ git config --global color.ui true

$ git config -l

## Basic demo
$ mkdir myweb

$ cd myweb

//create the loacl repository

$ git init

.... edit your local files

...

// check the status of your loacl folder

$ git status

//add your file to stage and prepare to commit

$ git add index.html

//check your status of folder again

$ git status

$ git commit -m "write down something you have changed"

$ git log /git log --oneline/ git log -p/git log --stat

## control your git
git add .

git reset Head xxx

git checkout -- xxxxx

git statuts

## compare your source
git add

git diff 

git diff --cached //when the changes have been added

## modify your last commit without a new commit
git commit --amend