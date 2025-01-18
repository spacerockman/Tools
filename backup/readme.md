## Basic

$ git init

$ git config -l

$ git config --global user.name "EricXu"

$ git config --global user.email "test@test.com"

$ git config --global color.ui true

$ git config -l

---

## ！！Workflow

- git checkout -b my-feature
- git diff
- git add
  - git add .
  - git add `<changed_file>`
- git commit
- git push origin my-feature
  - 👉If the remote main(master) branch changed during your working process
    - git checkout master
    - git pull origin master
    - git checkout my-feature
    - git rebase master 👉get lasted resource frommain(master) branch, ignoring my changes temporarily, might cause rebase conflicts which needs to be fixed manually.
    - git push -f origin my-feature
- create pull request
- manager would apply「◉Sqush and merge」
  - If the codes can be merged,

    - remote: delete the remote my-feature branch「◉delete branch」
    - local:delete the remote my-feature branch
      - git checkout master
      - git branch -D my-feature
      - git pull origin master

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

## cherry pick

git checkout master

git checkout -b xxxxxxxxxxx(branch_name)

//commitId ordered by timeline

git cherry-pick commitId1 commitId2 ...

git push origin xxxxxxxxxxx(branch_name)

//search the commitId of the file

git log --pretty=oneline filename
