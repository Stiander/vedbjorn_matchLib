# matchLib


### Description
This is a shared library contains core Vedbjørn functionality, needed for matching, route-handling and payment

### Technical Description


## Developers setup

 Add this submodule into the **/libs** folder of your service and use the functions, like this :

 * Open a git-terminal / bash, and navigate into the project root directory
 * If there is no folder named '/libs' here, then make it : >mkdir libs && cd libs
 * Now, add the library, as a git submodule : >git submodule add https://vedbjorn@bitbucket.org/vedbjorn/matchlib.git
 * Now you will see that the library is there, in the /libs folder
 * If there has been some developments to the library, after you have added it as a submodule, you can
 * update it manually like this : [project_root]>git submodule update --recursive --remote
 * ... or you can configure git to update automaticly : git config --global submodule.recurse true
 * Any update in this library, will not be reflected by a simple git pull, from projects that has this library as a submodule.
 * If you are going to make changes to the library, from the submodule of a project (which is a very likely scenario) , have these alternatives :
 * You can cd into the submodule from the serivce, and push manually.
 * ... or you can configure git to push automaticly : git config push.recurseSubmodules on-demand


## Notes

## Info and Support
Stian Broen @ Vedbjørn AS